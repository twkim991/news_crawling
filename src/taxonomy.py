TECH_CATEGORY_DEFS = {
    "AI/ML": (
        "artificial intelligence and machine learning technologies such as "
        "OpenAI, GPT, LLM, generative AI, PyTorch, TensorFlow, model training, "
        "model inference, NLP, computer vision, and recommendation systems"
    ),
    "Language": (
        "programming and query languages such as Python, Java, JavaScript, "
        "TypeScript, Go, Rust, C++, C#, PHP, Ruby, Kotlin, Swift, SQL, and "
        "other languages used to write software, scripts, applications, and data queries"
    ),
    "Framework": (
        "frameworks, libraries, runtimes, SDKs, and development platforms such as "
        "React, Next.js, Vue, Angular, Spring, Django, FastAPI, Express, Node.js, "
        ".NET, Laravel, Flutter, and development tools used to build applications and services"
    ),
    "DB/Storage": (
        "databases, caches, search engines, vector databases, object storage, and "
        "persistence technologies such as MySQL, PostgreSQL, MongoDB, Redis, "
        "Elasticsearch, OpenSearch, Cassandra, DynamoDB, S3, and storage engines"
    ),
    "Infra/Cloud": (
        "cloud and infrastructure technologies such as AWS, Azure, Google Cloud, "
        "hosting, networking, compute resources, virtual machines, containers, "
        "CDN, load balancers, and infrastructure services for running systems"
    ),
    "Data Engineering/Messaging": (
        "data engineering and messaging systems such as Kafka, Spark, Hadoop, Airflow, "
        "Flink, ETL, ELT, stream processing, data pipelines, warehousing, "
        "event-driven architecture, and messaging infrastructure"
    ),
    "DevOps/Automation": (
        "DevOps and automation tools such as Docker, Kubernetes, GitHub Actions, "
        "GitLab CI, Jenkins, Terraform, Ansible, CI/CD, orchestration, "
        "infrastructure as code, monitoring, observability, and workflow automation"
    ),
    "Security": (
        "cyber security technologies such as vulnerability management, malware detection, "
        "identity and access management, IAM, encryption, zero trust, application security, "
        "cloud security, endpoint security, threat detection, and security operations"
    ),
    "Collaboration/Utility": (
        "developer productivity and collaboration tools such as GitHub, GitLab, Jira, "
        "Confluence, Postman, Swagger, IDEs, package managers, testing frameworks, "
        "documentation tools, API tools, and general developer utility software"
    ),
    "Other Tech": (
        "general technology news about computing, software, hardware, devices, "
        "science, innovation, and technology that does not fit the other categories clearly"
    ),
}

SUBCATEGORY_MIN_SCORE = 0.30
SUBCATEGORY_MIN_GAP = 0.03