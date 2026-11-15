## Why I Started with Capabilities Before BPMN
Jumping directly into BPMN workflow modeling risks encoding Maple Crest Bank's legacy manual habits, such as re-keying T4/NOA figures and calculating ratios in spreadsheets, into the target flow. 
Following TOGAF and BIZBOK principles, I begand with a Business Capability Map to isolate *what* the bank must fundamentally accomplish independent of *who* performs the work or *which* system executes it.
Defining stable capabilities first establishes an architectural anchor aligned to Canadian regulatory mandates (OSFI B-20, CMHC, FINTRAC, and PIPEDA), ensuring the sunsequent BPMN process flows and Archimate application components are intentionally engineered for automation rather than patching broken manual handoffs. 

## Heatmap Takeways
Applying a capability heatmap directly links our $1.2 Million investment to Maple Crest Bank's primary operational bottlenecks. 
The three high friction capabilities (RED) represent manual re-keying and offline spreadsheet steps driving the 6.0 business days turnaround time and 14.0% applicant abandonment rate.
Automating these three capabilities unlocks the 75% prime salaried Straight-Through Processing (STP) target.
Meanwhile, addressing the ORANGE capabilities eliminates missing document loops at intake, directly driving down the 35% application rework rate toward the <10% target while maintaining strict FINTRACT compliance. 

## Data Lineage
Definiing passive Business Objects alongside our capabilities establishes a single canonical data model that bridges our EA to our analytics simulation. 
Every Business Object maps directly to the structured attributes required in our synthetic intake dataset.
Tracing how each capability reads or writes these objects gaurantees that the Python triage rules engine will evaluate the exact inputs needed to test OSFI MQR stress rates, CMHC premium capitalization, and the standardized exception codes without schema gaps. 
