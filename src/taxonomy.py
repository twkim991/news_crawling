TECH_CATEGORY_DEFS = {
    "AI/ML": (
        "artificial intelligence, AI, machine learning, ML, deep learning, neural networks, "
        "generative AI, large language models, LLM, foundation models, AI agents, AI assistants, "
        "natural language processing, NLP, computer vision, recommendation systems, "
        "model training, model inference, fine tuning, prompt engineering, "
        "retrieval augmented generation, RAG, embeddings, vector databases, "
        "인공지능, 머신러닝, 딥러닝, 생성형 AI, 대규모 언어모델, 자연어 처리, 컴퓨터 비전"
    ),

    "Programming Languages": (
        "programming languages and query languages such as Python, Java, JavaScript, TypeScript, "
        "Go, Rust, C, C++, C#, Kotlin, Swift, PHP, Ruby, Scala, SQL, GraphQL, "
        "language runtime, compilers, interpreters, language ecosystem, language updates, "
        "프로그래밍 언어, 개발 언어, 컴파일러, 인터프리터"
    ),

    "Frameworks & Libraries": (
        "software frameworks, libraries, SDKs, runtimes, and application platforms such as "
        "React, Next.js, Vue, Angular, Svelte, Spring, Spring Boot, Django, Flask, FastAPI, "
        "Express, Node.js, NestJS, .NET, ASP.NET, Laravel, Rails, Flutter, React Native, "
        "frontend frameworks, backend frameworks, application frameworks, package ecosystem, "
        "프레임워크, 라이브러리, 애플리케이션 개발 플랫폼"
    ),

    "Data & Databases": (
        "databases, storage systems, search engines, caching systems, and data platforms such as "
        "MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, OpenSearch, Cassandra, DynamoDB, "
        "Snowflake, BigQuery, data warehouse, data lake, ETL, ELT, data pipelines, "
        "stream processing, Kafka, Spark, Flink, Airflow, dbt, analytics platforms, "
        "데이터베이스, 데이터 플랫폼, 데이터 파이프라인, 데이터 분석"
    ),

    "Cloud & Infrastructure": (
        "cloud computing platforms and infrastructure technologies such as AWS, Azure, "
        "Google Cloud, server infrastructure, networking, CDN, DNS, virtual machines, "
        "containers, load balancers, edge computing, hosting services, platform services, "
        "cloud architecture, infrastructure platforms, "
        "클라우드 컴퓨팅, 서버 인프라, 네트워크 인프라, 데이터센터"
    ),

    "DevOps & Platform Engineering": (
        "DevOps practices, deployment automation, CI/CD pipelines, platform engineering, "
        "site reliability engineering, SRE, infrastructure as code, automation workflows, "
        "Docker, Kubernetes, Jenkins, GitHub Actions, GitLab CI, Terraform, Ansible, ArgoCD, "
        "monitoring, logging, tracing, observability, release automation, incident response, "
        "데브옵스, 배포 자동화, CI/CD, 플랫폼 엔지니어링"
    ),

    "Security": (
        "cybersecurity, information security, vulnerability management, zero day exploits, "
        "malware, ransomware, phishing, threat detection, security operations, "
        "identity and access management, IAM, authentication, authorization, encryption, "
        "application security, AppSec, DevSecOps, cloud security, data protection, privacy, "
        "사이버 보안, 정보 보안, 취약점, 암호화, 인증, 접근 제어"
    ),

    "Developer Tools & Collaboration": (
        "developer productivity tools, testing tools, API development tools, IDEs, "
        "version control systems, collaboration platforms, project management tools such as "
        "GitHub, GitLab, Jira, Confluence, Postman, Swagger, VS Code, IntelliJ, "
        "package managers such as npm, yarn, pnpm, pip, build tools, testing frameworks, "
        "documentation tools, code review tools, issue tracking systems, "
        "개발 도구, 협업 도구, 버전 관리, 코드 리뷰"
    ),

    "Mobile & Client Platforms": (
        "mobile development platforms and client application technologies such as "
        "Android, iOS, SwiftUI, Jetpack Compose, mobile SDKs, mobile app frameworks, "
        "cross platform apps, desktop client applications, front end client platforms, "
        "모바일 개발, 모바일 애플리케이션 플랫폼"
    ),

    "Tech Business & Industry": (
        "technology industry business news including product launches, company strategy, "
        "startup ecosystem, venture funding, acquisitions, mergers, developer market trends, "
        "platform competition, enterprise software market, product adoption, pricing models, "
        "technology companies, tech industry trends, "
        "기술 산업 동향, IT 산업, 스타트업 투자, 기술 기업 전략"
    ),

    "Other Tech": (
        "general technology news about software, hardware, computing systems, devices, "
        "innovation, science and technology developments that do not clearly fit "
        "into the other technology categories, "
        "일반 기술 뉴스, 소프트웨어와 하드웨어 관련 기술 동향"
    ),
}
SUBCATEGORY_MIN_SCORE = 0.30
SUBCATEGORY_MIN_GAP = 0.03