# What I've got so far
- Authentication
- GPT powered Chatbot as a Service with features:
    * Retrieval memory with Pinecone and OpenAI Embeddings
    * Function Calling with OpenAI API
    * Multitenancy via different namespaces on Pinecone, different Databases on FaunaDB and separated containers/lambda functions on AWS (Will decide on this later)

# What I would like
- A self service method for users to have only to embedd an snippet on their website to have a chatbot, this will include 1 Namespace, 1 Knowledgebase and 1 Database for the chatbot, user will have an UI to monitor and manage the chatbot
- A paid service that enables chatbots automations, custom integrations and multiple namespaces and knowledge bases.

# What I Lack
- The delivery mechanism of the technical capability to the user
- The data model for the business domain database of my own SaaS.