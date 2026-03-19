TECH_STACK_TAXONOMY = {
    "Programming Languages": {
        "description": (
            "programming languages, runtimes, compilers, package ecosystems, language standards, "
            "프로그래밍 언어, 런타임, 컴파일러"
        ),
        "stacks": {
            "Java": ["java", "openjdk", "jdk"],
            "Python": ["python", "cpython", "pypi"],
            "JavaScript": ["javascript", "ecmascript"],
            "TypeScript": ["typescript", "tsc"],
            "C++": ["c++", "cpp"],
            "C#": ["c#", ".net c#", "dotnet c#"],
            "Go": ["golang", "go language", "go 1.", "go runtime"],
            "Rust": ["rust", "cargo"],
            "Kotlin": ["kotlin"],
            "Swift": ["swift", "swiftlang"],
            "Dart": ["dart"],
        },
    },
    "Frameworks": {
        "description": (
            "frontend frameworks, backend frameworks, mobile frameworks, sdk ecosystems, "
            "프레임워크, 라이브러리, SDK"
        ),
        "stacks": {
            "Spring": ["spring framework", "spring", "spring boot"],
            "Django": ["django"],
            "FastAPI": ["fastapi"],
            "Express": ["express.js", "expressjs", "express"],
            "NestJS": ["nestjs", "nest.js"],
            "Ruby on Rails": ["ruby on rails", "rails framework", "ror"],
            "React": ["react", "reactjs"],
            "Vue": ["vue", "vue.js"],
            "Angular": ["angular"],
            "Svelte": ["svelte"],
            "Next.js": ["next.js", "nextjs"],
            "Flutter": ["flutter"],
            "React Native": ["react native"],
            "iOS SDK": ["ios sdk", "apple sdk", "xcode sdk"],
            "Android SDK": ["android sdk"],
        },
    },
    "Data & AI": {
        "description": (
            "machine learning, deep learning, llm platforms, generative ai, mlops, data science tooling, "
            "인공지능, 머신러닝, 생성형 AI, 데이터 처리, MLOps"
        ),
        "stacks": {
            "PyTorch": ["pytorch"],
            "TensorFlow": ["tensorflow", "keras"],
            "Scikit-learn": ["scikit-learn", "sklearn"],
            "Pandas": ["pandas"],
            "NumPy": ["numpy"],
            "OpenAI": ["openai", "chatgpt", "gpt-4", "gpt-4.1", "gpt-4o", "o1", "o3"],
            "Hugging Face": ["hugging face", "transformers", "diffusers"],
            "LangChain": ["langchain", "langgraph"],
            "MLflow": ["mlflow"],
            "Kubeflow": ["kubeflow"],
        },
    },
    "Databases & Storage": {
        "description": (
            "rdbms, nosql, caching, search indexing, storage engines, "
            "데이터베이스, 스토리지, 검색 인덱스"
        ),
        "stacks": {
            "PostgreSQL": ["postgresql", "postgres"],
            "MySQL": ["mysql"],
            "Oracle": ["oracle database", "oracle db", "oracle"],
            "MongoDB": ["mongodb", "mongo db"],
            "Cassandra": ["cassandra", "apache cassandra"],
            "DynamoDB": ["dynamodb", "dynamo db"],
            "Redis": ["redis"],
            "Memcached": ["memcached"],
            "Elasticsearch": ["elasticsearch", "elastic stack"],
            "OpenSearch": ["opensearch", "open search"],
        },
    },
    "Infrastructure & Cloud": {
        "description": (
            "cloud providers, containers, orchestration, hosting, compute infrastructure, "
            "클라우드, 인프라, 컨테이너, 오케스트레이션"
        ),
        "stacks": {
            "AWS": ["aws", "amazon web services", "ec2", "s3", "bedrock"],
            "Google Cloud": ["google cloud", "gcp"],
            "Azure": ["azure", "microsoft azure", "azure openai"],
            "Naver Cloud": ["naver cloud", "ncloud"],
            "Docker": ["docker", "docker desktop"],
            "Kubernetes": ["kubernetes", "k8s"],
        },
    },
    "Data Engineering & Messaging": {
        "description": (
            "streaming, batch processing, data pipelines, analytics engineering, messaging systems, "
            "데이터 엔지니어링, 메시징, ETL, 스트림 처리"
        ),
        "stacks": {
            "Kafka": ["kafka", "apache kafka"],
            "Spark": ["spark", "apache spark", "pyspark"],
            "dbt": ["dbt", "data build tool"],
        },
    },
    "DevOps & CI/CD": {
        "description": (
            "continuous integration, deployment automation, observability, infrastructure as code, "
            "CI/CD, 데브옵스, 관측성, IaC"
        ),
        "stacks": {
            "GitHub Actions": ["github actions"],
            "GitLab CI": ["gitlab ci", "gitlab pipeline"],
            "Jenkins": ["jenkins"],
            "Terraform": ["terraform", "opentofu"],
            "Ansible": ["ansible"],
            "Prometheus": ["prometheus"],
            "Grafana": ["grafana"],
        },
    },
    "Collaboration & Tools": {
        "description": (
            "developer productivity, collaboration, ide tooling, api tooling, package management, "
            "개발 도구, 협업 도구, IDE, API 도구"
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
    "Other Tech": {
        "description": (
            "general software and technology news that is related to tech but does not map to a tracked stack, "
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
STACK_MIN_HITS = 1
STACK_MAX_TAGS = 5
