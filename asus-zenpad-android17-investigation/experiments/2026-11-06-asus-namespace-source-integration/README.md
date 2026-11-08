# Namespace source integration

Question: can the tested P00A linker namespace repair be integrated into the product source without changing its kernel, policy permissions or preserved images?

Status: parent-reviewed source transaction; native rebuilding remains separate. The patch retains SYSTEM providers in the dedicated system namespace and removes only the duplicate advertisements from the gated legacy vendor default.

Inputs: frozen namespace handoff v1, patch d7c6088b233ebb0d893e46816768d11798609c499a8b64337ccf98843bb4abcc. The genuine before-failure, fixed/non-P00A tests and enforcing runtime progress are preserved in the producing spike.

Outputs: exact source payload and integration journal, with original preimages retained on the builder. No device, kernel, policy-permission, output-image or native build operation is included.

Continuation: after the separately tested power-supply filter repair is available, perform one ordinary combined image build and repeat semantic/runtime checks. The isolated candidate's successful runtime is not proof that the final rebuilt APEX or physical tablet works.
