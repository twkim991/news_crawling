import re


TECH_STACK_TAXONOMY = {
    "Programming Languages": {
        "description": (
            "programming languages, runtimes, compilers, package ecosystems, language standards, "
            "프로그래밍 언어, 런타임, 컴파일러"
        ),
        "subgroups": {
            "Languages": {
                "Python": ["python", "cpython", "pypi"],
                "JavaScript": ["javascript", "ecmascript", "js"],
                "TypeScript": ["typescript", "tsc", "ts"],
                "C#": ["c#", "csharp", ".net c#", "dotnet c#"],
                "C++": ["c++", "cpp"],
                "C": [" c language ", " ansi c ", " c programming ", "language c", "c lang"],
                "Java": ["java", "openjdk", "jdk"],
                "Kotlin": ["kotlin"],
                "PHP": ["php"],
                "Swift": ["swift", "swiftlang"],
                "Rust": ["rust", "cargo"],
                "Go": ["golang", "go language", "go runtime", "go 1.", "language go"],
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
                "React": ["react", "reactjs"],
                "Angular": ["angular"],
                "Vue": ["vue", "vue.js"],
                "Svelte": ["svelte"],
                "Next.js": ["next.js", "nextjs"],
                "Nuxt.js": ["nuxt.js", "nuxtjs", "nuxt"],
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
                "Node.js": ["node.js", "nodejs", "node js"],
                "Express": ["express", "express.js", "expressjs"],
                "Django": ["django"],
                "FastAPI": ["fastapi"],
                "Spring Boot": ["spring boot", "springboot"],
                "ASP.NET Core": ["asp.net core", "asp net core", "aspnet core"],
                "Deno": ["deno"],
                "Laravel": ["laravel"],
                "Rails": ["ruby on rails", "rails", "rails framework", "ror"],
                "Flask": ["flask"],
                "NestJS": ["nestjs", "nest.js", "nest js"],
                "Axum": ["axum"],
                "Actix-Web": ["actix-web", "actix web", "actix_web"],
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
            "컨테이너, 오케스트레이션, 인프라, 데브옵스"
        ),
        "subgroups": {
            "Containers / Orchestration": {
                "Docker": ["docker", "dockerfile", "docker desktop"],
                "Kubernetes": ["kubernetes", "k8s"],
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