MCP builder POC prototype

System Description AI prompt

Prototype uses github and fasmcp.cloud
Actual implementation will use codecommit and lambda
You are currently building the prototype

Participants aka folder structure:
  - Cookie cutter app
  - Test suite
  - MCP Builder as Builder
    - Infrastructure
    - Builds (builder store)
    - mcp
    - pipeline
  - LLM
    - Infrastructure
    - Guardrails
  - Store
    - For now this is a subfolder in builder, but should be separated
  - Host
    - Infrastructure
    - Deploy

Definitions of each

  - Is a github repository
    - The github repository should be created and managed using terraform
    - The github repository should be linked to fastmcp.cloud for auto deployment

1. Builder
  - Prequisites
    - Cookie cutter app with OAuth
    - Tests that ensure OAuth part is working after LLM has injected code
    - Ability to deploy to github
  - Is an MCP server
  - Is behind OAuth, which means we receive an Auth token header that contains the email
    - The email should map to a uuid in the the mcp builder app
  - Is an MCPGR
  - Two tools
    - Is building an MCP server viable?
      - Returns tat the following required params are to be passed to the build tool
        - What is the platform name?
        - What are the OAuth creds
          - ClientID
          - Secret
          - RedirectURL
    - Build an MCP server
      - Receives above required params
      - Ask LLM to assess API
        - If not possible
          - Log feature request
          - Return message to agent to pass to user that it won't be built but has been noted
        - If valid
          - Return message to agent to pass to user that it is being built
          - Pipeline triggered async
            - Creates a submodule at builds/<uuid>/<platform>/<version>/
              - Stored at 
                - builds/<uuid>/<platform>/<version>/prompt.txt
                - builds/<uuid>/<platform>/<version>/mcp/<cookie-cutter>
                  - Has a cookie cut app layout for consistency
              - Stores the instructions in builds/<uuid>/<platform>/<version>/prompt.txt
              - Passes the cookie cut app and instructions to the LLM to build the MCP server
              - Runs unit tests against the code returned by the LLM
              - If the tests fail, we adjust the prompt and try again until the tests pass.
              - When the tests pass, deploy the code to the Store
              - When deployed and live, send email to the user
                - Tool is deployed
                - Where to access it and how to add it to toqan
          - Versioning
            - Each call to the build tool by the same user for the same platform creates a new version
            - i.e. end of create results in version 1
            - version 2 is an update to version 1
            - in other words, each builder pipeline results in one version being generated
              - even if the LLM is called multiple times
            - The LLM should take all previous versions and prompts into consideration

2. LLM
  - Hosted LLM [TODO: Decide on host and LLM]
  - Guardrail context provided by builder
    - We pass it a cookie cut app
  - LLM writes code that builds a new MCP server in the cookie cutter framework
    - LLM looks up api of platform
    - LLM implements an MCP based on
      - Prompt
        - The guardrails prompt
      - Template
        - The cookie cutter framework app
        - The previous version (determines version from file system)
      - Calculated
        - The API docs of the platform
    - Output to:
      - builds/<uuid>/<platform>/<version>/prompt.txt
      - builds/<uuid>/<platform>/<version>/mcp/...
  - Arguments:
    - Platform
    - Cookie cutter framework app
    - Guardrails prompt

3. Store
    - In the builder repo under folder called builds.
      - builds/<uuid>/<platform>/<version>/prompt.txt
      - builds/<uuid>/<platform>/<version>/mcp/...

4. Host
  - We do not provision this infrastructure usually, but for the POC we will.
  - Auto push builds/uuid to a new MCPGR
