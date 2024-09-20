# What is a readme


compile the circuit 
```bash
 circom health-record/HealthRecordVerification.circom --r1cs --wasm --sym

```
Result:

```bash
template instances: 1
non-linear constraints: 1
linear constraints: 0
public inputs: 0
private inputs: 2
public outputs: 1
wires: 4
labels: 6
```

For Health Risk Assessment

```bash
circom risk/HealthRiskAssessment.circom --r1cs --wasm --sym -l C:/Users/CCL/Desktop/circomlib/circuits
```
Result:

```bash
template instances: 73
non-linear constraints: 346
linear constraints: 0
public inputs: 0
private inputs: 4
public outputs: 1
wires: 349
labels: 732
```

PLONK Trusted Setup (No Ceremony Needed!)
Unlike Groth16, PLONK does not require a circuit-specific trusted setup. Instead, you will only need a universal setup that can be used across multiple circuits.

Generate the Powers of Tau (Universal Setup):

```bash

snarkjs powersoftau new bn128 12 pot12_0000.ptau

snarkjs powersoftau contribute pot12_0000.ptau pot12_final.ptau
```
The above commands generate and finalize the Powers of Tau file (pot12_final.ptau). If that gives error, download powers of tau from: 


## Setup Phase for PLONK
Now, generate the proving and verification keys for your circuits.

- For HealthRecordVerification:

```bash
snarkjs plonk setup HealthRecordVerification.r1cs powersOfTau28_hez_final_12.ptau HealthRecordVerification.zkey
```

- For HealthRiskAssessment:

```bash
snarkjs plonk setup HealthRiskAssessment.r1cs  powersOfTau28_hez_final_12.ptau HealthRiskAssessment.zkey
```
 
Export the .vkey from the .zkey: Use the following command to export the verification key (.vkey) from the .zkey file:

```bash
snarkjs zkey export verificationkey HealthRecordVerification.zkey HealthRecordVerification.vkey

```

```bash
snarkjs zkey export verificationkey HealthRiskAssessment.zkey HealthRiskAssessment.vkey

```


## Generate Witness

For HealthRecordVerification

```bash
snarkjs wtns calculate HealthRecordVerification_js/HealthRecordVerification.wasm input_healthrecord.json witness_healthrecord.wtns

```


## Generate Proof

For HealthRecordVerification:

```bash
snarkjs plonk prove HealthRecordVerification.zkey witness_healthrecord.wtns proof_healthrecord.json public_healthrecord.json
```

## Verify Proof

For HealthRecordVerification:
```bash
snarkjs plonk verify HealthRecordVerification.vkey public_healthrecord.json proof_healthrecord.json
```