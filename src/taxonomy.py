# taxonomy.py

import re


TECH_STACK_TAXONOMY = {
    "Programming Languages": {
        "description": (
            "programming languages, runtimes, compilers, package ecosystems, language standards, "
            "프로그래밍 언어, 런타임, 컴파일러"
        ),
        "subgroups": {
            "Languages": {
                "Python": ["python", "cpython", "pypi", "python 3", "파이썬"],
                "JavaScript": ["javascript", "ecmascript", "js", "자바스크립트"],
                "TypeScript": ["typescript", "tsc", "ts", "타입스크립트"],
                "C#": ["c#", "csharp", ".net c#", "dotnet c#"],
                "C++": ["c++", "cpp"],
                "C": [" c language ", " ansi c ", " c programming ", "language c", "c lang"],
                "Java": ["java", "openjdk", "jdk", "자바"],
                "Kotlin": ["kotlin", "코틀린"],
                "PHP": ["php"],
                "Swift": ["swift", "swiftlang", "스위프트"],
                "Rust": ["rust", "rustlang", "rust-lang", "러스트"],
                "Go": ["golang", "go language", "go runtime", "go 1.", "language go", "고언어", "golang", "go 언어"],
                "Ruby": ["ruby"],
            }
        },
    },
    "Frontend Frameworks": {
        "description": (
            "frontend frameworks, ui libraries, meta-frameworks, web application frameworks, "
            "프론트엔드 프레임워크, UI 라이브러리"
        ),
        "subgroups": {
            "Frontend": {
                "React": ["react", "reactjs", "react.js", "리액트"],
                "Angular": ["angular", "앵귤러"],
                "Vue": ["vue", "vue.js", "뷰", "뷰js"],
                "Svelte": ["svelte", "스벨트"],
                "Next.js": ["next.js", "nextjs", "넥스트js", "넥스트"],
                "Nuxt.js": ["nuxt.js", "nuxtjs", "nuxt", "넉스트", "눅스트"],
            }
        },
    },
    "Backend Frameworks": {
        "description": (
            "backend frameworks, web servers, api frameworks, server-side application frameworks, "
            "백엔드 프레임워크, API 프레임워크, 서버 프레임워크"
        ),
        "subgroups": {
            "Backend": {
                "Node.js": ["node.js", "nodejs", "node js", "노드js", "노드"],
                "Express": ["express", "express.js", "expressjs", "익스프레스"],
                "Django": ["django", "장고"],
                "FastAPI": ["fastapi", "패스트api"],
                "Spring Boot": ["spring boot", "springboot", "스프링 부트", "스프링부트"],
                "ASP.NET Core": ["asp.net core", "asp net core", "aspnet core"],
                "Deno": ["deno"],
                "Laravel": ["laravel"],
                "Rails": ["ruby on rails", "rails", "rails framework", "ror"],
                "Flask": ["flask"],
                "NestJS": ["nestjs", "nest.js", "nest js", "네스트js"],
                "Axum": ["axum"],
                "Actix Web": ["actix-web", "actix web", "actix_web"],
                "Rocket": ["rocket", "rocket.rs", "rocket framework"],
                "Bun": ["bun", "bun.sh"],
                "Prisma": ["prisma", "prisma orm"],
            }
        },
    },
    "Mobile": {
        "description": (
            "mobile application frameworks and cross-platform mobile development ecosystems, "
            "모바일 앱 프레임워크, 크로스플랫폼 개발"
        ),
        "subgroups": {
            "Mobile Frameworks": {
                "React Native": ["react native", "react-native"],
                "Flutter": ["flutter"],
            }
        },
    },
    "AI / ML": {
        "description": (
            "machine learning, deep learning, ai frameworks, model training, data science tooling, "
            "인공지능, 머신러닝, 딥러닝 프레임워크"
        ),
        "subgroups": {
            "ML / DL Frameworks": {
                "PyTorch": ["pytorch", "torch"],
                "TensorFlow": ["tensorflow", "tf", "keras"],
                "Scikit-learn": ["scikit-learn", "sklearn"],
            }
        },
    },
     "Infrastructure & DevOps": {
        "description": (
            "containers, orchestration, deployment infrastructure, cloud-native operations, "
            "ci/cd, infrastructure as code, devops automation, "
            "컨테이너, 오케스트레이션, 인프라, 데브옵스, CI/CD, IaC"
        ),
        "subgroups": {
            "Containers / Orchestration": {
                "Docker": ["docker", "dockerfile", "docker desktop"],
                "Kubernetes": ["kubernetes", "k8s"],
            },
            "CI/CD & IaC": {
                "Jenkins": ["jenkins", "젠킨스", "jenkins pipeline", "jenkinsfile"],
                "GitHub Actions": ["github actions", "github workflow", "github workflows", "깃허브 액션", "깃허브 액션스"],
                "GitLab CI/CD": ["gitlab ci", "gitlab ci/cd", "gitlab pipeline", "gitlab pipelines", "깃랩 ci/cd", "깃랩 파이프라인"],
                "Terraform": ["terraform", "hashicorp terraform", "terraform module", "terraform state", "테라폼"],

            },
        },
    },
    "Data / DB": {
        "description": (
            "relational databases, nosql databases, in-memory data stores, database engines, "
            "관계형 데이터베이스, NoSQL 데이터베이스, 인메모리 저장소, 데이터베이스 엔진"
        ),
        "subgroups": {
            "Databases": {
                "PostgreSQL": ["postgresql", "postgres", "psql", "포스트그레sql", "포스트그레스", "포스트그레"],
                "MySQL": ["mysql", "마이에스큐엘", "my sql"],
                "SQLite": ["sqlite", "sqlite3", "sqlite 3"],
                "Microsoft SQL Server": ["microsoft sql server", "sql server", "mssql", "ms sql server", "ssms", "마이크로소프트 sql 서버"],
                "Redis": ["redis", "redis cache", "레디스"],
                "MongoDB": ["mongodb", "mongo db", "몽고db", "몽고 디비"],
            }
        },
    },
    "Data Engineering & Streaming": {
        "description": (
            "streaming systems, workflow orchestration, big data processing, distributed data pipelines, "
            "데이터 엔지니어링, 스트리밍, 워크플로우, 빅데이터 처리"
        ),
        "subgroups": {
            "Data / Messaging": {
                "Kafka": ["kafka", "apache kafka"],
                "Spark": ["spark", "apache spark", "pyspark"],
                "Airflow": ["airflow", "apache airflow"],
                "Hadoop": ["hadoop", "apache hadoop"],
            }
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


STACK_DISAMBIGUATION = {
    "Python": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "cpython", "pypi", "python 3", "python package", "python packages",
            "django", "fastapi", "flask", "pandas", "numpy", "scipy",
            "script", "scripting", "interpreter", "jupyter", "notebook",
            "pip", "virtualenv", "poetry", "pyproject", "pytest",
            "machine learning", "data science",

            "파이썬", "파이썬 패키지", "파이썬 라이브러리", "인터프리터",
            "주피터", "노트북", "데이터 사이언스", "머신러닝",
        ],
        "negative_keywords": [
            "snake", "snakes", "venom", "venomous", "bite", "bites",
            "reptile", "reptiles", "serpent", "serpents",
            "blood", "antivenom", "species", "wildlife", "zoology",
            "python snake", "python meat", "python skin", "Monty",

            "비단뱀", "뱀", "파충류", "독사", "야생동물",
        ],
        "supporting_entities": ["python software foundation", "pypi", "cpython", "anaconda" "파이썬 소프트웨어 재단"],
    },
    "React": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "reactjs", "react.js", "react native", "jsx", "tsx",
            "react native", "vite", "frontend", "front-end", "next.js", "web app", "npm", 
        ],
        "negative_keywords": [
            "reacts", "reacted", "reacting", "reaction", "reactions",
            "reactor", "reactors", "react to", "market reacts",
            "fans react", "people react", "overreact", "interactive", "reacts with", "reacts to", "reacted to", "reacting to", "people react", "fans react", "overreact", "interactive",

            "리액트", "리액트 네이티브", "프론트엔드", "웹앱", "컴포넌트", "상태관리",
        ],
        "supporting_entities": ["meta", "reactjs", "react native", "jsx", "메타"],
    },
    "Vue": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "vue.js", "nuxt", "frontend", "component", "composition api", "vite",
            "뷰", "뷰js", "프론트엔드", "컴포넌트",
        ],
        "negative_keywords": [
            "view", "views", "viewer", "point of view"
        ],
        "supporting_entities": ["vue.js", "nuxt", "vite"],
    },
    "Rocket": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "rocket.rs", "rocket framework", "rust", "rustlang",
            "web framework", "crate", "crates.io", "backend", "server",
        ],
        "negative_keywords": [
            "rocket launch", "rocket launches", "rocket attack", "rocket fire",
            "missile", "missiles", "spacex", "nasa", "orbital", "booster",
            "spacecraft", "launch vehicle", "space X",
        ],
        "supporting_entities": ["rocket.rs", "rust foundation", "crates.io"],
    },
    "Docker": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "container", "containers", "image", "images", "docker compose", "compose", "dockerfile",
            "registry", "kubernetes", "k8s", "daemon", "desktop", "engine", "swarm", "hub", "devops",
        ],
        "negative_keywords": [
            "ship", "ships", "shipping", "vessel", "marine", "harbor", "harbour", "port authority",
            "cargo", "dockworker", "dock worker", "dockyard", "wharf", "navy", "boatyard", "cruise",
            "ferry", "boat", "boats", "maritime", "seaport", "container ship", "voodoo", "hoodoo",
            "ritual", "religion",
        ],
        "supporting_entities": ["docker inc", "docker hub", "moby", "mirantis"],
    },
    "Go": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "golang", "gopher", "compiler", "runtime", "package", "packages", "module", "modules",
            "stdlib", "garbage collector", "goroutine", "goroutines", "concurrency", "go team",
        ],
        "negative_keywords": [
            "go ahead", "go home", "go live", "go through", "go on", "go with", "go back",
            "let's go", "lets go", "going to", "gone",
        ],
        "supporting_entities": ["google", "google go", "golang"],
    },
    "Swift": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "apple", "swiftui", "xcode", "ios", "macos", "iphone", "ipad", "package manager",
            "app store", "objective-c", "cocoa",
        ],
        "negative_keywords": [
            "taylor swift", "swiftly", "singer", "album", "concert", "tour", "fans", "bird", "birds", "SwiftCurrentOnline.com"
        ],
        "supporting_entities": ["apple", "swiftui", "xcode"],
    },
    "Spark": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "apache", "apache spark", "pyspark", "databricks", "dataframe", "streaming", "cluster",
            "etl", "big data", "sql", "driver", "executor",
        ],
        "negative_keywords": [
            "sparked", "sparks", "spark interest", "spark debate", "ignite", "ignited", "romance",
            "chemistry", "wildfire", "spark driver"
        ],
        "supporting_entities": ["apache", "databricks"],
    },
    "Rails": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "ruby", "rubygems", "gem", "gems", "activerecord", "actionpack", "hotwire",
            "controller", "view", "model", "web app",
        ],
        "negative_keywords": [
            "railway", "rail", "station", "subway", "train", "trains", "commuter", "metro",
            "tram", "freight", "locomotive",
        ],
        "supporting_entities": ["ruby", "rubyonrails", "basecamp", "37signals"],
    },
    "Express": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "node", "node.js", "middleware", "router", "rest api", "server", "backend", "javascript",
            "typescript", "http server",
        ],
        "negative_keywords": [
            "express delivery", "express train", "express bus", "expressway", "express lane", "courier", "air express", "bank", "adobe express", "adobe", "fedex", "ups",
            "parcel", "shipping", "train", "trains", "subway", "subways", "pharmacy", "delivery", "delivering", "panda express", "Gazeta Express", "lbc express", "dhl express",
        ],
        "supporting_entities": ["node.js", "npm", "javascript"],
    },
    "Bun": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "bun.sh", "runtime", "javascript", "typescript", "package manager", "bundler", "node",
            "transpiler", "oven-sh",
        ],
        "negative_keywords": [
            "hamburger bun", "bun hairstyle", "hair bun", "bakery", "bread", "pastry", "roll",
        ],
        "supporting_entities": ["bun.sh", "oven", "oven-sh"],
    },
    "Rust": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "cargo", "cargo.toml", "cargo.lock",
            "rustc", "crate", "crates", "crates.io",
            "borrow checker", "ownership", "lifetimes",
            "memory safety", "systems programming",
            "rustlang", "rust-lang", "rust foundation",
            "mozilla", "ffi", "tokio", "actix", "axum",
            "wasm", "webassembly"
        ],
        "negative_keywords": [
            "corrosion", "oxide", "oxidation", "rusting", "rusted", "rusty",
            "weathered", "decay", "metal", "iron", "steel",
            "rust belt", "auto industry", "car body", "bridge", "pipe"
        ],
        "supporting_entities": [
            "rust foundation", "rustlang", "rust-lang", "mozilla", "crates.io"
        ],
    },
    "Kafka": {
        "ambiguous": True,
        "requires_context": False,
        "context_keywords": [
            "apache kafka", "broker", "brokers", "topic", "topics", "consumer", "producer", "streaming",
            "confluent", "event streaming",
        ],
        "negative_keywords": ["franz kafka", "novel", "novelist", "literature", "writer"],
        "supporting_entities": ["apache", "confluent"],
    },
    "PHP": {
        "ambiguous": True,
        "requires_context": False,
        "context_keywords": [
            "php", "php language", "php runtime", "php package", "php framework",
            "laravel", "symfony", "codeigniter", "cakephp",
        ],
        "negative_keywords": ["Partial Hospitalization Program", "public housing program", "personal health plan"],
        "supporting_entities": ["Laravel", "Symfony", "CodeIgniter", "CakePHP"],
    },
     "Jenkins": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "ci/cd", "pipeline", "deploy", "deployment", "automation",
            "jenkins pipeline", "jenkinsfile",

            "배포", "배포 자동화", "파이프라인", "ci/cd", "빌드 자동화",
        ],
        "negative_keywords": [],
        "supporting_entities": ["cloudbees", "jenkinsfile", "젠킨스"],
    },
    "Terraform": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "iac", "infrastructure as code", "hashicorp", "terraform module",
            "terraform state", "terraform plan", "terraform apply",

            "인프라 자동화", "코드형 인프라", "프로비저닝", "테라폼", "해시코프",
        ],
        "negative_keywords": [],
        "supporting_entities": ["hashicorp", "hcp", "해시코프"],
    },
    "Microsoft SQL Server": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "mssql", "microsoft sql server", "ssms", "sql server agent",
            "t-sql", "transact-sql", "sql server management studio", "sql server reporting services",
        ],
        "negative_keywords": [],
        "supporting_entities": ["microsoft", "azure data studio", "sql server management studio"],
    },
    "Redis": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "cache", "caching", "in-memory", "key-value", "pub/sub", "replica",
            "cluster", "redis cache", "redis server",

            "캐시", "인메모리", "키값", "레디스", "레디스 캐시", "클러스터",
        ],
        "negative_keywords": [],
        "supporting_entities": ["redis labs", "redis inc", "레디스"],
    },
    "MongoDB": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "document database", "nosql", "atlas", "bson", "collection",
            "문서형 데이터베이스", "nosql", "컬렉션", "몽고db",
        ],
        "negative_keywords": [],
        "supporting_entities": ["mongodb atlas", "mongo db", "몽고db"],
    },
    "PostgreSQL": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "postgresql", "postgres", "psql", "database", "sql", "extension",
            "데이터베이스", "sql", "포스트그레sql", "포스트그레스", "psql",
        ],
        "negative_keywords": [],
        "supporting_entities": ["postgresql", "postgres", "포스트그레sql"],
    },
    "MySQL": {
        "ambiguous": True,
        "requires_context": True,
        "context_keywords": [
            "mysql", "database", "sql", "mysql server", "mysql shell",
            "데이터베이스", "sql", "마이에스큐엘",
        ],
        "negative_keywords": [],
        "supporting_entities": ["oracle", "mysql", "마이에스큐엘"],
    },
}


STACK_VENDOR_SIGNALS = {
    "React": ["meta", "jsx", "component", "components", "react native", "frontend", "메타", "컴포넌트", "프론트엔드"],
    "Docker": ["docker inc", "docker hub", "dockerfile", "container", "도커", "컨테이너"],
    "Kubernetes": ["cncf", "pod", "cluster", "helm", "kubelet", "쿠버네티스", "파드", "클러스터"],
    "PyTorch": ["meta", "tensor", "training", "inference", "메타", "학습", "추론"],
    "Spark": ["apache", "databricks", "pyspark", "아파치", "데이터브릭스"],
    "Rails": ["ruby", "activerecord", "rubygems"],
    "Express": ["node.js", "middleware", "router", "노드js", "미들웨어", "라우터"],
    "Python": ["pypi", "cpython", "python software foundation", "pip", "파이썬", "파이파이", "주피터"],
    "Rocket": ["rocket.rs", "crate", "crates.io", "rust", "러스트"],

    "Jenkins": ["cloudbees", "jenkinsfile", "pipeline", "agent", "젠킨스", "파이프라인"],
    "GitHub Actions": ["github", "workflow", "workflow dispatch", "runner", "깃허브", "워크플로", "러너"],
    "GitLab CI/CD": ["gitlab", "pipeline", "runner", ".gitlab-ci.yml", "깃랩", "파이프라인", "러너"],
    "Terraform": ["hashicorp", "iac", "provider", "state", "해시코프", "코드형 인프라", "프로바이더"],
    "PostgreSQL": ["postgresql", "postgres", "psql", "포스트그레sql", "포스트그레스"],
    "MySQL": ["mysql", "mysql server", "mysql shell", "마이에스큐엘"],
    "SQLite": ["sqlite", "sqlite3"],
    "Microsoft SQL Server": ["microsoft", "mssql", "ssms", "t-sql", "마이크로소프트", "sql 서버"],
    "Redis": ["redis", "cache", "in-memory", "레디스", "캐시", "인메모리"],
    "MongoDB": ["mongodb", "document database", "atlas", "bson", "몽고db", "문서형 데이터베이스"],
}


STACK_EVENT_KEYWORDS = [
    "release", "released", "launch", "launched", "patch", "patched", "upgrade", "upgraded",
    "migration", "deprecated", "deprecation", "support", "lts", "rc", "beta", "preview",
    "cve", "vulnerability", "security fix", "changelog", "sdk", "framework", "runtime",
]


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
                disambiguation = STACK_DISAMBIGUATION.get(stack_name, {})
                stack_aliases[stack_name] = {
                    "category": category,
                    "subgroup": subgroup,
                    "aliases": aliases,
                    "ambiguous": bool(disambiguation.get("ambiguous", False)),
                    "requires_context": bool(disambiguation.get("requires_context", False)),
                    "context_keywords": tuple(disambiguation.get("context_keywords", [])),
                    "negative_keywords": tuple(disambiguation.get("negative_keywords", [])),
                    "supporting_entities": tuple(disambiguation.get("supporting_entities", [])),
                    "vendor_signals": tuple(STACK_VENDOR_SIGNALS.get(stack_name, [])),
                }

    return stack_aliases


def _alias_to_regex(alias: str) -> re.Pattern[str]:
    escaped = re.escape(alias.lower())
    escaped = escaped.replace(r"\ ", r"\s+")

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
STACK_SCORE_THRESHOLD = 3.0
PRIMARY_STACK_MIN_SCORE = 5.0
PRIMARY_STACK_MIN_MARGIN = 1.5
