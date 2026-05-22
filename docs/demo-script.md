# DiffShield demo script

1. Open the homepage.
2. Explain that DiffShield is a lightweight repo threat modeler shaped around a world-model-lite architecture.
3. Click `Run sample repo scan`.
4. On the scan detail page, explain:
   - assets and relationships are the world model
   - candidate attack paths come from deterministic rules
   - findings are validated and normalized
   - trace events make the pipeline explainable
5. Walk through the critical admin route finding first.
6. Then show:
   - root container
   - exposed internal admin port
   - env secret hygiene
   - broad db access path
7. Close with:
   - next integration step is PR diffs or deployment hooks
   - same architecture can move from local demo DB to Postgres and Docker

