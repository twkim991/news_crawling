TECH_CATEGORY_DEFS = {
    "AI/ML": (
        "artificial intelligence and machine learning technologies such as "
        "OpenAI, ChatGPT, GPT, Claude, Anthropic, Gemini, LLM, generative AI, "
        "AI agents, AI assistant, AI coding assistant, Copilot, Cursor, Windsurf, "
        "model training, model inference, fine-tuning, prompt engineering, "
        "retrieval augmented generation, RAG, embeddings, vector databases for AI, "
        "natural language processing, NLP, computer vision, recommendation systems, "
        "deep learning, neural networks, PyTorch, TensorFlow, Hugging Face, AI automation"
    ),
    "Programming Languages": (
        "programming and query languages such as Python, Java, JavaScript, TypeScript, "
        "Go, Rust, C, C++, C#, Kotlin, Swift, PHP, Ruby, Scala, SQL, GraphQL, "
        "language syntax, compilers, interpreters, language ecosystem, language updates"
    ),
    "Frameworks & Libraries": (
        "application development frameworks, libraries, runtimes, SDKs, and app platforms such as "
        "React, Next.js, Vue, Angular, Svelte, Spring, Spring Boot, Django, Flask, FastAPI, "
        "Express, Node.js, NestJS, .NET, ASP.NET, Laravel, Rails, Flutter, React Native, "
        "build tools, package ecosystem, frontend frameworks, backend frameworks"
    ),
    "Data & Databases": (
        "databases, storage, search, caching, analytics, and data systems such as "
        "MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, OpenSearch, Cassandra, "
        "DynamoDB, Snowflake, BigQuery, data warehouse, data lake, ETL, ELT, "
        "data pipeline, stream processing, Kafka, Spark, Flink, Airflow, dbt, "
        "vector database, search engine, storage systems"
    ),
    "Cloud & Infrastructure": (
        "cloud computing and infrastructure technologies such as AWS, Azure, Google Cloud, "
        "server infrastructure, networking, CDN, DNS, virtual machines, containers, "
        "load balancers, edge computing, hosting, infrastructure services, platform services, "
        "Kubernetes infrastructure, cloud platform architecture"
    ),
    "DevOps & Platform Engineering": (
        "DevOps, deployment, automation, CI/CD, platform engineering, observability, "
        "site reliability engineering, SRE, workflow automation, infrastructure as code, "
        "Docker, Kubernetes, Jenkins, GitHub Actions, GitLab CI, Terraform, Ansible, "
        "ArgoCD, monitoring, logging, tracing, incident response, release automation, cron jobs"
    ),
    "Security": (
        "cyber security and information security such as vulnerability management, "
        "zero day, malware, ransomware, phishing, IAM, identity and access management, "
        "encryption, authentication, authorization, endpoint security, network security, "
        "application security, AppSec, DevSecOps, cloud security, threat detection, "
        "security operations, data protection, privacy, compliance"
    ),
    "Developer Tools & Collaboration": (
        "developer productivity, testing, API tools, IDEs, collaboration platforms, "
        "source control, project management, and general engineering tools such as "
        "GitHub, GitLab, Jira, Confluence, Postman, Swagger, VS Code, IntelliJ, "
        "package managers, npm, yarn, pnpm, pip, testing frameworks, documentation tools, "
        "code review tools, issue tracking, team collaboration tools"
    ),
    "Mobile & Client Platforms": (
        "mobile development and client application platforms such as Android, iOS, "
        "SwiftUI, Jetpack Compose, mobile SDKs, mobile app frameworks, cross-platform apps, "
        "desktop clients, app store ecosystem, front-end client platform technologies"
    ),
    "Tech Business & Industry": (
        "technology company strategy, product launch, startup ecosystem, funding, acquisition, "
        "developer market trends, platform competition, pricing, product adoption, "
        "technology industry business news, enterprise software market, company roadmap"
    ),
    "Other Tech": (
        "general technology news about software, hardware, computing, devices, science, "
        "innovation, and technology topics that do not fit clearly into the other categories"
    ),
}

SUBCATEGORY_MIN_SCORE = 0.30
SUBCATEGORY_MIN_GAP = 0.03