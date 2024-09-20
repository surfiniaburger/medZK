import os
import shutil
from flask import Flask, request, jsonify, render_template
import subprocess
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()



app = Flask(__name__)

# Google Gemini API setup
api_key = os.getenv('API_KEY')
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    safety_settings=safety_settings,
    generation_config=generation_config,
    system_instruction="You are SOD, a health therapist and medical assistant, answering only health-related questions."
)

chat_session = model.start_chat(history=[])

def generate_proof(circuit):
    try:
        # Make 'circom' a subfolder of your script
        CIRCUIT_BASE_DIR = os.path.join(os.path.dirname(__file__), r'backend\circom')



        if circuit == "HealthRecordVerification":
            wasm_path = os.path.join(CIRCUIT_BASE_DIR, "HealthRecordVerification_js", "HealthRecordVerification.wasm")
            input_json = os.path.join(CIRCUIT_BASE_DIR,  "input_healthrecord.json")
            witness_wtns = os.path.join(CIRCUIT_BASE_DIR,  "witness_healthrecord.wtns")
            zkey = os.path.join(CIRCUIT_BASE_DIR, "HealthRecordVerification.zkey")
            js_script = os.path.join(CIRCUIT_BASE_DIR, "HealthRecordVerification_js", "generate_witness.js")
        

        elif circuit == "HealthRiskAssessment":
            wasm_path = os.path.join(CIRCUIT_BASE_DIR, "HealthRiskAssessment_js", "HealthRiskAssessment.wasm")
            input_json = os.path.join(CIRCUIT_BASE_DIR, "input.json")
            witness_wtns = os.path.join(CIRCUIT_BASE_DIR, "witness.wtns")
            zkey = os.path.join(CIRCUIT_BASE_DIR,  "HealthRiskAssessment.zkey")
            js_script = os.path.join(CIRCUIT_BASE_DIR, "HealthRiskAssessment_js", "generate_witness.js")
        else:
            return None, "Invalid circuit selection."
        
        # Check if all required files exist
        required_files = [wasm_path, input_json, witness_wtns, zkey, js_script]
        for file in required_files:
            if not os.path.exists(file):
                return None, f"File not found: {file}"
            
        # Check if node and snarkjs are accessible
        if not shutil.which('node'):
            return None, "'node' executable not found in PATH."
        if not shutil.which('snarkjs'):
            return None, "'snarkjs' executable not found in PATH."
        
        # Print paths for debugging
        print("Running Node.js script:", js_script)
        print("WASM path:", wasm_path)
        print("Input JSON path:", input_json)
        print("Witness path:", witness_wtns)
        print("Zkey path:", zkey)

        # Run witness generation using the correct js script path
        result = subprocess.run(['node', js_script, wasm_path, input_json, witness_wtns], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode())
        print(result.stderr.decode())
        
        # Generate proof using PLONK
        subprocess.run(['snarkjs', 'plonk', 'prove', zkey, witness_wtns, 'proof.json', 'public.json'], check=True)
        
        # Load proof and public signals
        with open(os.path.join(CIRCUIT_BASE_DIR, 'proof.json')) as proof_file:
            proof = json.load(proof_file)
        with open(os.path.join(CIRCUIT_BASE_DIR, 'public.json')) as public_file:
            public_signals = json.load(public_file)

        return {"proof": proof, "publicSignals": public_signals}, None

    except subprocess.CalledProcessError as e:
        # Log any error returned by the subprocess
        print(f"Subprocess error: {e.stderr.decode()}")
        return None, f"Error during subprocess execution: {e.stderr.decode()}"
    except Exception as e:
        return None, str(e)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate-proof', methods=['POST'])
def generate_proof_endpoint():
    data = request.json
    print(f"Received data: {data}")  # Log received data
    circuit = data.get("circuit")
    proof_data, error = generate_proof(circuit)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(proof_data)

@app.route('/query', methods=['POST'])
def query():
    question = request.form.get('question')
    proof = request.form.get('proof')
    public_signals = request.form.get('public_signals')

    try:
        # Verify proof (skipped here for simplicity)
        response = chat_session.send_message(question)
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)