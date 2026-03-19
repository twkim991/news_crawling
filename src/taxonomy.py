import re


TECH_STACK_TAXONOMY = {
    "Programming Languages": {
        "description": (
            "programming languages, runtimes, compilers, package ecosystems, language standards, "
            "프로그래밍 언어, 런타임, 컴파일러"
        ),
        "subgroups": {
            "Languages": {
                "Java": ["java", "openjdk", "jdk"],
                "Python": ["python", "cpython", "pypi"],
                "JavaScript": ["javascript", "ecmascript"],
                "TypeScript": ["typescript", "tsc"],
                "C++": ["c++", "cpp"],
                "C#": ["c#", ".net c#", "dotnet c#"],
                "Go": ["golang", "go language", "go runtime", "go 1."],
                "Rust": ["rust", "cargo"],
                "Kotlin": ["kotlin"],
                "Swift": ["swift", "swiftlang"],
                "Dart": ["dart"],
            }
        },
    },
    "Frameworks": {
        "description": (
            "frontend frameworks, backend frameworks, mobile frameworks, sdk ecosystems, "
            "프레임워크, 라이브러리, SDK"
        ),
        "subgroups": {
            "Backend": {
                "Spring": ["spring framework", "spring boot", "spring"],
                "Django": ["django"],
                "FastAPI": ["fastapi"],
                "Express": ["express.js", "expressjs", "express"],
                "NestJS": ["nestjs", "nest.js"],
                "Ruby on Rails": ["ruby on rails", "rails framework", "ror"],
            },
            "Frontend": {
                "React": ["react", "reactjs"],
                "Vue": ["vue", "vue.js"],
                "Angular": ["angular"],
                "Svelte": ["svelte"],
                "Next.js": ["next.js", "nextjs"],
            },
            "Mobile": {
                "Flutter": ["flutter"],
                "React Native": ["react native"],
                "iOS SDK": ["ios sdk", "apple sdk", "xcode sdk"],
                "Android SDK": ["android sdk"],
            },
        },
    },
    "Data & AI": {
        "description": (
            "machine learning, deep learning, llm platforms, generative ai, mlops, data science tooling, "
            "인공지능, 머신러닝, 생성형 AI, 데이터 처리, MLOps"
        ),
        "subgroups": {
            "ML / DL Framework": {
                "PyTorch": ["pytorch"],
                "TensorFlow": ["tensorflow", "keras"],
                "Scikit-learn": ["scikit-learn", "sklearn"],
            },
            "Data Analysis / Processing": {
                "Pandas": ["pandas"],
                "NumPy": ["numpy"],
            },
            "LLM / Generative AI": {
                "OpenAI": ["openai", "chatgpt", "gpt-4", "gpt-4.1", "gpt-4o", "o1", "o3"],
                "Hugging Face": ["hugging face", "transformers", "diffusers"],
                "LangChain": ["langchain", "langgraph"],
            },
            "MLOps / Serving": {
                "MLflow": ["mlflow"],
                "Kubeflow": ["kubeflow"],
            },
        },
    },
    "Databases & Storage": {
        "description": (
            "rdbms, nosql, caching, search indexing, storage engines, "
            "데이터베이스, 스토리지, 검색 인덱스"
        ),
        "subgroups": {
            "RDBMS": {
                "PostgreSQL": ["postgresql", "postgres"],
                "MySQL": ["mysql"],
                "Oracle": ["oracle database", "oracle db", "oracle"],
            },
            "NoSQL": {
                "MongoDB": ["mongodb", "mongo db"],
                "Cassandra": ["cassandra", "apache cassandra"],
                "DynamoDB": ["dynamodb", "dynamo db"],
            },
            "Cache / In-Memory": {
                "Redis": ["redis"],
                "Memcached": ["memcached"],
            },
            "Search / Index": {
                "Elasticsearch": ["elasticsearch", "elastic stack"],
                "OpenSearch": ["opensearch", "open search"],
            },
        },
    },
    "Infrastructure & Cloud": {
        "description": (
            "cloud providers, containers, orchestration, hosting, compute infrastructure, "
            "클라우드, 인프라, 컨테이너, 오케스트레이션"
        ),
        "subgroups": {
            "Cloud Providers": {
                "AWS": ["aws", "amazon web services", "ec2", "s3", "bedrock"],
                "Google Cloud": ["google cloud", "gcp"],
                "Azure": ["azure", "microsoft azure", "azure openai"],
                "Naver Cloud": ["naver cloud", "ncloud"],
            },
            "Containers & Orchestration": {
                "Docker": ["docker", "docker desktop"],
                "Kubernetes": ["kubernetes", "k8s"],
            },
            "Serverless / Edge": {
                "AWS Lambda": ["aws lambda", "lambda function", "lambda"],
                "Cloudflare Workers": ["cloudflare workers", "workers"],
            },
            "Networking / CDN": {
                "Cloudflare": ["cloudflare"],
                "Vercel": ["vercel"],
            },
        },
    },
    "Data Engineering & Messaging": {
        "description": (
            "streaming, batch processing, data pipelines, analytics engineering, messaging systems, "
            "데이터 엔지니어링, 메시징, ETL, 스트림 처리"
        ),
        "subgroups": {
            "Streaming / Messaging": {
                "Kafka": ["kafka", "apache kafka"],
                "RabbitMQ": ["rabbitmq"],
                "ActiveMQ": ["activemq", "active mq"],
            },
            "Big Data Processing": {
                "Spark": ["spark", "apache spark", "pyspark"],
                "Flink": ["flink", "apache flink"],
                "Hadoop": ["hadoop", "apache hadoop"],
            },
            "Data Pipeline / Workflow": {
                "Airflow": ["airflow", "apache airflow"],
                "Prefect": ["prefect"],
                "dbt": ["dbt", "data build tool"],
            },
        },
    },
    "DevOps & CI/CD": {
        "description": (
            "continuous integration, deployment automation, observability, infrastructure as code, "
            "CI/CD, 데브옵스, 관측성, IaC"
        ),
        "subgroups": {
            "CI/CD": {
                "GitHub Actions": ["github actions"],
                "GitLab CI": ["gitlab ci", "gitlab pipeline"],
                "Jenkins": ["jenkins"],
                "ArgoCD": ["argocd", "argo cd"],
            },
            "Monitoring / Observability": {
                "Prometheus": ["prometheus"],
                "Grafana": ["grafana"],
                "Datadog": ["datadog"],
            },
            "Logging": {
                "ELK Stack": ["elk stack", "elasticsearch logstash kibana", "logstash kibana"],
            },
            "Infrastructure as Code": {
                "Terraform": ["terraform", "opentofu"],
                "Ansible": ["ansible"],
            },
        },
    },
    "Collaboration & Tools": {
        "description": (
            "developer productivity, collaboration, ide tooling, api tooling, package management, "
            "개발 도구, 협업 도구, IDE, API 도구"
        ),
        "subgroups": {
            "Version Control": {
                "GitHub": ["github", "copilot"],
                "GitLab": ["gitlab"],
            },
            "Project / Docs": {
                "Jira": ["jira", "atlassian jira"],
                "Confluence": ["confluence"],
                "Notion": ["notion"],
            },
            "API Tools": {
                "Postman": ["postman"],
                "Swagger": ["swagger", "openapi"],
            },
            "IDE / Editors": {
                "VS Code": ["vs code", "vscode", "visual studio code"],
                "IntelliJ": ["intellij", "jetbrains"],
            },
            "Package Managers": {
                "npm": ["npm"],
                "pnpm": ["pnpm"],
            },
        },
    },
    "Other Tech": {
        "description": (
            "general software and technology news that is related to tech but does not map to a tracked stack, "
            "일반 기술 뉴스, 기술 정책"
        ),
        "subgroups": {},
    },
}


def _build_category_defs() -> dict[str, str]:
    return {
        category: ", ".join(
            [info["description"]]
            + [subgroup for subgroup in info["subgroups"]]
            + [alias for stacks in info["subgroups"].values() for aliases in stacks.values() for alias in aliases]
        )
        for category, info in TECH_STACK_TAXONOMY.items()
    }


def _build_stack_aliases() -> dict[str, dict[str, object]]:
    stack_aliases = {}

    for category, info in TECH_STACK_TAXONOMY.items():
        for subgroup, stacks in info["subgroups"].items():
            for stack_name, aliases in stacks.items():
                stack_aliases[stack_name] = {
                    "category": category,
                    "subgroup": subgroup,
                    "aliases": aliases,
                }

    return stack_aliases


def _alias_to_regex(alias: str) -> re.Pattern[str]:
    escaped = re.escape(alias.lower())

    # 공백은 가변 공백 허용
    escaped = escaped.replace(r"\ ", r"\s+")

    # 영문/숫자 위주 키워드는 단어 경계 보강
    if re.fullmatch(r"[a-z0-9\.\+#\-\s]+", alias.lower()):
        pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    else:
        pattern = escaped

    return re.compile(pattern, re.IGNORECASE)


def _get_stack_patterns() -> dict[str, dict[str, object]]:
    patterns = {}

    for stack_name, info in STACK_ALIASES.items():
        patterns[stack_name] = {
            "category": info["category"],
            "subgroup": info["subgroup"],
            "patterns": [_alias_to_regex(alias) for alias in info["aliases"]],
        }

    return patterns


TECH_CATEGORY_DEFS = _build_category_defs()
STACK_ALIASES = _build_stack_aliases()
SUBCATEGORY_MIN_SCORE = 0.30
SUBCATEGORY_MIN_GAP = 0.03
STACK_MIN_HITS = 1
STACK_MAX_TAGS = 5