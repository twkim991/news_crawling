TECH_STACK_TAXONOMY = {
    "AI/ML": {
        "description": (
            "artificial intelligence, machine learning, generative AI, large language models, agent systems, "
            "multimodal models, vector search, model serving, inference optimization, AI platforms, "
            "인공지능, 머신러닝, 생성형 AI, LLM, 모델 서빙, AI 플랫폼"
        ),
        "stacks": {
            "OpenAI": ["openai", "chatgpt", "gpt-4", "gpt-4.1", "gpt-4o", "o1", "o3"],
            "Anthropic": ["anthropic", "claude"],
            "Google Gemini": ["gemini", "vertex ai", "google ai studio"],
            "Meta Llama": ["llama", "meta ai"],
            "Hugging Face": ["hugging face", "transformers", "diffusers"],
            "LangChain": ["langchain", "langgraph"],
            "PyTorch": ["pytorch"],
            "TensorFlow": ["tensorflow", "keras"],
            "Ollama": ["ollama"],
            "Vector DB": ["pinecone", "weaviate", "milvus", "faiss", "chromadb", "qdrant"],
        },
    },
    "Programming Languages": {
        "description": (
            "programming languages, runtimes, compilers, interpreters, package ecosystems, language standards, "
            "프로그래밍 언어, 런타임, 컴파일러"
        ),
        "stacks": {
            "Python": ["python", "cpython", "pypi"],
            "Java": ["java", "openjdk", "jdk"],
            "JavaScript": ["javascript", "ecmascript"],
            "TypeScript": ["typescript", "tsc"],
            "Go": ["golang", "go language", "go 1."],
            "Rust": ["rust", "cargo"],
            "Kotlin": ["kotlin"],
            "Swift": ["swift", "swiftlang"],
            "C#": ["c#", ".net c#"],
            "SQL": ["sql", "postgres sql", "mysql sql"],
        },
    },
    "Frameworks & Libraries": {
        "description": (
            "application frameworks, frontend frameworks, backend frameworks, SDKs, libraries, developer runtimes, "
            "프레임워크, 라이브러리, SDK"
        ),
        "stacks": {
            "React": ["react", "reactjs"],
            "Next.js": ["next.js", "nextjs"],
            "Vue": ["vue", "vue.js"],
            "Angular": ["angular"],
            "Node.js": ["node.js", "nodejs"],
            "Spring": ["spring framework", "spring", "spring boot"],
            "Django": ["django"],
            "FastAPI": ["fastapi"],
            "Flutter": ["flutter"],
            "React Native": ["react native"],
        },
    },
    "Data & Databases": {
        "description": (
            "databases, warehouses, stream processing, ETL, analytics engineering, search platforms, data pipelines, "
            "데이터베이스, 데이터 파이프라인, 분석 플랫폼"
        ),
        "stacks": {
            "PostgreSQL": ["postgresql", "postgres"],
            "MySQL": ["mysql"],
            "MongoDB": ["mongodb", "mongo db"],
            "Redis": ["redis"],
            "Elasticsearch": ["elasticsearch", "elastic stack"],
            "Kafka": ["kafka", "apache kafka"],
            "Spark": ["spark", "apache spark", "pyspark"],
            "Snowflake": ["snowflake"],
            "BigQuery": ["bigquery", "big query"],
            "dbt": ["dbt", "data build tool"],
        },
    },
    "Cloud & Infrastructure": {
        "description": (
            "cloud platforms, compute infrastructure, networking, hosting, containers, edge, platform services, "
            "클라우드, 인프라, 호스팅, 컨테이너"
        ),
        "stacks": {
            "AWS": ["aws", "amazon web services", "ec2", "s3", "bedrock"],
            "Azure": ["azure", "microsoft azure", "azure openai"],
            "Google Cloud": ["google cloud", "gcp"],
            "Cloudflare": ["cloudflare", "workers"],
            "Vercel": ["vercel"],
            "Netlify": ["netlify"],
            "Docker": ["docker", "docker desktop"],
            "Kubernetes": ["kubernetes", "k8s"],
            "OpenShift": ["openshift"],
            "VMware": ["vmware", "vsphere"],
        },
    },
    "DevOps & Platform Engineering": {
        "description": (
            "continuous integration, deployment automation, platform engineering, observability, infrastructure as code, "
            "CI/CD, 데브옵스, 플랫폼 엔지니어링"
        ),
        "stacks": {
            "GitHub Actions": ["github actions"],
            "GitLab CI": ["gitlab ci", "gitlab pipeline"],
            "Jenkins": ["jenkins"],
            "Terraform": ["terraform", "opentofu"],
            "Ansible": ["ansible"],
            "ArgoCD": ["argocd", "argo cd"],
            "Prometheus": ["prometheus"],
            "Grafana": ["grafana"],
            "Datadog": ["datadog"],
            "Sentry": ["sentry"],
        },
    },
    "Security": {
        "description": (
            "application security, cloud security, identity, access control, threat detection, encryption, incident response, "
            "보안, 인증, 접근 제어, 위협 탐지"
        ),
        "stacks": {
            "CrowdStrike": ["crowdstrike"],
            "Okta": ["okta"],
            "Cloud Security": ["wiz", "lacework", "prisma cloud"],
            "Vault": ["vault", "hashicorp vault"],
            "Auth0": ["auth0"],
        },
    },
    "Developer Tools & Collaboration": {
        "description": (
            "developer productivity, IDEs, source control, code review, testing, API tooling, package management, "
            "개발 도구, 협업 도구, IDE, 테스트 도구"
        ),
        "stacks": {
            "GitHub": ["github", "copilot"],
            "GitLab": ["gitlab"],
            "Jira": ["jira", "atlassian"],
            "Postman": ["postman"],
            "Swagger": ["swagger", "openapi"],
            "VS Code": ["vs code", "vscode", "visual studio code"],
            "IntelliJ": ["intellij", "jetbrains"],
            "npm": ["npm"],
            "pnpm": ["pnpm"],
        },
    },
    "Mobile & Client Platforms": {
        "description": (
            "mobile application development, native app platforms, client frameworks, mobile SDKs, "
            "모바일 개발, 클라이언트 플랫폼"
        ),
        "stacks": {
            "Android": ["android", "jetpack compose"],
            "iOS": ["ios", "swiftui"],
            "Flutter": ["flutter"],
            "React Native": ["react native"],
        },
    },
    "Tech Business & Industry": {
        "description": (
            "technology industry strategy, product launches, developer ecosystem competition, platform pricing, enterprise adoption, "
            "기술 산업 전략, 플랫폼 경쟁, 제품 출시"
        ),
        "stacks": {
            "OpenAI Ecosystem": ["openai", "chatgpt", "api pricing"],
            "AWS Ecosystem": ["aws", "bedrock", "amazon web services"],
            "Microsoft Ecosystem": ["microsoft", "github", "azure"],
            "Google Ecosystem": ["google cloud", "gemini", "android"],
        },
    },
    "Other Tech": {
        "description": (
            "general technology news about software, hardware, policy, and innovation that does not map cleanly to a stack, "
            "일반 기술 뉴스, 기술 정책"
        ),
        "stacks": {},
    },
}


def _build_category_defs() -> dict[str, str]:
    category_defs = {}
    for category, info in TECH_STACK_TAXONOMY.items():
        alias_terms = []
        for aliases in info["stacks"].values():
            alias_terms.extend(aliases)
        category_defs[category] = ", ".join([info["description"], *alias_terms])
    return category_defs


def _build_stack_aliases() -> dict[str, dict[str, object]]:
    stack_aliases = {}
    for category, info in TECH_STACK_TAXONOMY.items():
        for stack_name, aliases in info["stacks"].items():
            stack_aliases[stack_name] = {
                "category": category,
                "aliases": aliases,
            }
    return stack_aliases


TECH_CATEGORY_DEFS = _build_category_defs()
STACK_ALIASES = _build_stack_aliases()
SUBCATEGORY_MIN_SCORE = 0.30
SUBCATEGORY_MIN_GAP = 0.03
