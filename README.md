# Embodatahub · Embodied Data Engineering Platform

**From raw capture to trained policy — one pipeline, end to end.**

*Every frame of your data deserves to be trained on.*

> Dataset QC Workbench · Seven quality filters · VLM semantic evaluation
> Bidirectional conversion across five mainstream formats · 3D replay verification

Developed by **Ningbo TsingtaoAI Intelligent Technology Co., Ltd.** — *Forge Robotic Intelligence*

---

## The Problem: Your Robot Data Is Slowing Down Your Models

Your algorithm team burns weekends tuning hyperparameters. Your data team burns weekends scrubbing episodes.
More often than not, the bottleneck isn't the algorithm — it's the data.

**01 · Data is buried in file shares**
Thousands of files, and nobody can say which ones are actually trainable. Organizing by *file* is fundamentally at odds with what a model needs, which is *episodes*.

**02 · Bad data slips into the training set**
Failed grasps, idle spinning, collision jitter, dropped objects — these invalid trials can only be found by a human playing back every episode. Meanwhile, they are quietly poisoning your model.

**03 · Timestamps don't line up**
Cameras at 30 Hz, joints at 500 Hz, plus oscillator drift and network latency. Every channel keeps its own time. The model learns causal relationships that were never true.

**04 · Format conversion is manual labor**
LeRobot, RLDS, HDF5, Zarr — five teams, five formats. One-off conversion scripts get rewritten over and over, and still crash halfway through a training run.

**05 · Annotation cost eats the budget**
Purely manual cleaning and labeling means standards drift, and costs explode the moment you scale. Small and mid-sized teams simply cannot absorb it.

**06 · When something breaks, you can only guess**
The model underperforms — is it the algorithm or the data? Without visualization or reports, you are left with trial and error.

---

## The Answer: Let the Platform Decide Whether Data Is Usable

Embodatahub is a **data engineering foundation for embodied AI**. It takes the data-governance work scattered across file shares, ad-hoc scripts, and tribal knowledge, and pulls it into a single standardized, reproducible, auditable automated pipeline.

**See it.** Multi-view video, joint curves, gripper open/close, and 3D trajectories replayed in sync — what your data looks like, at a glance.

**Filter it precisely.** Seven quality filters plus VLM semantic judgment score and grade every episode automatically. Bad data stops before it reaches training.

**Export it.** Five mainstream training formats convert bidirectionally. Export and go — no more one-off compatibility scripts.

> Data engineering should not be an algorithm team's side project. Hand it to the platform, and let your algorithm engineers get back to algorithms.

---

## Product Map: Six Capabilities Across the Full Data Lifecycle

| Stage | Capability |
|---|---|
| **Data Ingestion** | Multi-format recognition across projects, missions, and files |
| **Intelligent QC** | Seven filters + VLM semantic evaluation |
| **Visual Replay** | Rerun 3D replay + reporting dashboard |
| **Task Orchestration** | Asynchronous queues, Worker clusters |
| **Format Export** | One-click bidirectional conversion across five formats |
| **Training Integration** | Ready integration with leading training and simulation stacks |

**Dataset QC Workbench (RDS)** — The last quality gate before training: import, inspect, review, export. Fully web-based.

**Spark Studio — 3D Scene Visualization** — Gaussian-splatting scene rendering and sensor trajectory replay, turning abstract data into a place you can actually see.

**Task Queue & Automated Pipelines** — Asynchronous scheduling, online worker registration, and format-conversion and content-extraction pipelines out of the box.

**Data Management Platform** — Projects / missions / files organized in three tiers, with a permission system, API keys, search, and statistics.

**Model Training Integration** — Connects to world models, OpenVLA, LeRobot, FluxVLA, and other mainstream training stacks.

**Simulation Environment Integration** — Integrates Isaac Lab, Unitree RL Lab, and SurRoL, managing real and simulated data in one place.

---

## Core Capability 01 — Seven Quality Filters, a Full Health Check

One run, seven dimensions checked in parallel. Every episode receives a weighted composite score.

**01 · Visual Quality**
Laplacian variance for blur, pixel-mean checks for over/under-exposure, inter-frame MSE for frozen frames — with evidence frames and timeline visualization.

**02 · Sudden-Change Detection**
Velocity, acceleration, and jerk computed after median filtering and Savitzky-Golay smoothing, with median + MAD robust statistics to surface anomalous jumps.

**03 · Temporal Synchronization**
Validates frame-interval deviation against nominal fps, actual-vs-nominal duration, and the start/end offset between video streams and the data stream.

**04 · Extreme-Value Detection**
Physical bounds established from dataset-wide 1% / 99% quantiles and IQR, with automatic exemption for legitimate behaviors such as gripper saturation.

**05 · Kinematic Consistency**
Loads the URDF model and uses Pinocchio forward kinematics to recompute end-effector poses, verifying that joint states and recorded end-effector poses are physically self-consistent.

**06 · Orientation Alignment**
Aligns position and orientation data through a rotation-correction matrix, removing systematic bias introduced by differing coordinate frames.

**07 · Metadata Completeness**
Six health checks: task description, camera naming conventions, resolution consistency, multi-view coverage, action fields, and episode integrity.

### Scoring and Decision

| Verdict | Threshold | Meaning |
|---|---|---|
| **Passed** | score ≥ 0.8 | Meets quality bar; directly usable for training |
| **Review** | 0.6 ≤ score < 0.8 | Questionable; requires human judgment |
| **Excluded** | score < 0.6 | Critical defects; should be removed from the training set |

---

## Core Capability 02 — Bringing a Large Model into the QC Pipeline

*What numerical checks cannot catch, hand to a vision-language model.*

Numerical detection can find anomalies in curves, but it cannot read what is happening in a frame. Was the robot *placing a block into a box*, or just *waving its arm in circles*? That requires something that can actually understand the image.

Embodatahub integrates VLMs into the QC loop: it automatically extracts key frames from each episode, sends them to a vision-language model to judge task success, and returns both a confidence score and a rationale. Failed grasps, dropped objects, incomplete motions — nothing slips through.

**Three integration paths supported**

- **OpenAI-compatible endpoints** — including self-hosted inference services
- **Google Gemini** — `gemini-2.5-flash`
- **Local inference** — data never leaves the intranet

When the VLM judges an episode as failed, the system automatically upgrades its status from *Passed* to *Review*. Better one extra human confirmation than one bad episode slipping through.

**Tunable sampling** — extract 1–12 frames per episode to trade cost against precision.
**Custom prompts** — the evaluation prompt is editable, with a `{task}` placeholder auto-filled from the task description.
**Adjustable weighting** — VLM results carry an independently configurable weight, fused with the numerical filters.

---

## Core Capability 03 — Five Formats in Free Flow, Export to Train

**Import**

| Format | Description |
|---|---|
| **LeRobot v3** | HuggingFace community standard |
| **ACT HDF5** | ALOHA and other dual-arm manipulation datasets |
| **robomimic HDF5** | robomimic framework format |
| **UMI Zarr** | Universal Manipulation Interface format |

**Export**

| Format | Description |
|---|---|
| **LeRobot v3 / v2.1** | Community standard, either version |
| **ACT HDF5** | Directly usable for dual-arm manipulation training |
| **robomimic HDF5** | Single-file delivery |
| **UMI Zarr** | Directory or archive |

**Export scope and artifacts**

- **Selective** — checked items / passed only / review only / excluded only / all indexed
- **Conversion report** — `conversion_report.json` records field mappings and metadata completeness
- **Human override** — manual decisions are preserved above automatic scores, and take precedence

---

## Core Capability 04 — QC You Can See, Problems With Nowhere to Hide

**Rerun 3D Replay**
Select a suspect episode and generate a replay file in one click: the end-effector's 3D trajectory, per-joint position and velocity curves, gripper open/close state, and multi-camera video aligned on a shared timeline.

**Cleaning Report Dashboard**
Total episodes, total frames, total duration, frame rate, and composite score in a single overview. A quality-distribution histogram is color-coded by passed / review / excluded — anomalies are obvious at a glance.

**Signal Curves and Duration Distribution**
Interactive SVG line charts show gripper dimensions over time; episode duration distributions come with a mean reference line, so abnormally short or long segments surface on their own.

**Evidence Frames and Timeline**
Every finding ships with a representative evidence frame and a timeline position. Conclusions are backed by evidence — no more arguing from intuition.

---

## Core Capability 05 — Local-First: Compliance Before Scale

**Local-first architecture.** The QC workbench runs on *your* machine. Datasets stay on your own disks and are never uploaded to the cloud. Import, inspection, replay, and export all complete locally — teams with data-privacy and compliance requirements don't have to choose between efficiency and confidentiality.

**Engineering details we also got right**

- **Source data is read-only.** The platform never modifies your original datasets. Cleaning state, replay recordings, exports, and reports are written to a separate artifact directory — always traceable, always cleanable.
- **Local inference optional.** VLM evaluation can connect to a local inference service, so sensitive imagery never leaves the intranet while still benefiting from large-model semantic QC.
- **Fully self-hostable.** Containerized one-command deployment, supporting private cloud and on-premises bare metal. It runs completely without any external cloud service.

> The raw data your robots collect is often your most sensitive — and most valuable — asset. It should not have to leave your data center just to get a quality check.

---

## Core Capability 06 — Automated Pipelines That Pull People Out of Repetitive Work

**File ingestion** → upload triggers an event
**Task enqueue** → asynchronous scheduling with priority management
**Worker execution** → online registration, status reported back
**Automatic processing** → parsing / conversion / content extraction
**Result write-back** → metadata updated, status synchronized

**Task templates out of the box.** Data validation, metadata extraction, BAG→MCAP conversion, visual SLAM, and point-cloud segmentation are built in as templates — no need to write from scratch.

**Online worker management.** Compute nodes auto-register and report heartbeats, with live online status. A node going down is detected promptly, so scheduling decisions rest on real information.

**Seamless handoff from upload to QC.** Once a file lands, its metadata is parsed and it is registered in the index, flowing straight into the QC pipeline's candidate queue with no manual shuttling.

**One-command deployment.** The full service stack comes up through a single unified startup script — frontend, backend API, QC workbench, 3D visualization, and task queue all in place, with no component-by-component manual startup.

---

## Workflow: One Pipeline, A Dataset's Entire Life

```
01 Collect      →  02 Ingest   →  03 QC
   Teleop rig /      Files land in     Seven filters +
   cart / robot      object storage,   VLM auto-score
   multimodal        metadata          and grade
   recording         registered

04 Review       →  05 Export   →  06 Train
   3D replay +       Five formats      Connect to leading
   report review,    convert in one    training frameworks
   human overrides   click, with a     and simulation
   auto verdicts     conversion report environments
```

From a raw recording file to a dataset you can feed straight into a policy network — all within one platform. No more crossing tools, scripts, and handoffs between people.

**A glimpse of a typical scenario.** A 10-minute dual-arm grasping recording lands in the platform. The system automatically segments it into multiple independent manipulation episodes, sends aligned key frames to a vision-language model to generate action descriptions, flags the first failed episode as *grasp failure*, and gives the remaining successful episodes high ratings. The engineer only needs to confirm in the browser — then pick a format and export.

---

## Platform: Not Just a QC Tool, a Complete Data Platform

**Project and data organization** — Manage robot data in a project / mission / file structure, with tagging, classification, and metadata extension. Data assets stay clearly discoverable.

**Multi-format ingestion** — Native support for ROS bag, MCAP, ZED SVO2, and other common robot capture formats, preserving original semantics without lossy re-encoding.

**Permissions and access control** — User groups and role management with resource-level fine-grained access control, balancing team collaboration against data isolation.

**Open APIs and keys** — An API-key system and open interfaces let external systems integrate programmatically, fitting into your existing R&D workflow.

**Global data search** — Unified browsing and search across projects, missions, files, and metadata. Finding data no longer means digging through directories.

**Bilingual interface** — Chinese / English switching, with preferences persisted locally. Collaboration across domestic and international teams is friction-free.

> Tools solve point problems. Platforms solve collaboration problems. Embodatahub's goal is to let an entire team work around one shared, trustworthy body of data.

---

## Ecosystem: Fits Your Training Stack, Fits Your Simulator

**Model Training**

| Stack | Purpose |
|---|---|
| **World Models** | 3DGS scene model training |
| **OpenVLA** | Vision-language-action model fine-tuning |
| **LeRobot** | HuggingFace robotics learning library (ACT / Diffusion / TDMPC) |
| **FluxVLA** | Full-stack VLA engineering platform |

**Simulation Validation**

| Framework | Purpose |
|---|---|
| **Isaac Lab** | GPU-accelerated robot simulation |
| **Unitree RL Lab** | Unitree robot reinforcement learning |
| **SurRoL** | Surgical robotics RL platform |
| **AERIS-10** | Open-source phased-array radar system |

**Real and simulated, managed as one.** The platform treats real teleoperation data and simulation-generated data as equals: unified archival, unified QC, unified export. You can mix real and simulated data in any ratio to assemble a training set, using synthetic data to dilute the high cost of real-world collection.

---

## Architecture: Built for Massive Multimodal Data

**Control and data planes are separated.** Business control flows through the API gateway; large file data flows directly to object storage. The two paths never drag each other down.

**Containerized deployment.** Full-stack container orchestration means consistent environments and easy migration. Self-hostable on private cloud or on-premises bare metal.

| Layer | Components |
|---|---|
| **Application** | Vue 3 + Quasar admin UI · Dataset QC Workbench · 3D Scene Visualization |
| **Intelligence** | Seven quality filters · VLM semantic evaluation · Multimodal timestamp alignment |
| **Scheduling** | Asynchronous task queue · Worker node registration · Hybrid compute scheduling |
| **Storage** | Distributed object storage (S3-compatible) · Relational metadata DB · In-memory cache |
| **Infrastructure** | Container orchestration · Service health checks · Structured logging and status monitoring |

### Technology Stack

| Area | Stack |
|---|---|
| Backend control | TypeScript · NestJS · TypeORM · PostgreSQL · Elasticsearch |
| Storage & cache | SeaweedFS (S3 API mode) · Redis · Redis Cluster |
| Task queue | BullMQ · Redis Streams · Node.js Queue Consumer |
| Compute engine | Python 3.10+ · PyArrow · Pandas · NumPy · OpenCV · Docker |
| AI & algorithms | PyTorch · Qwen2-VL / vLLM · LeRobot · Rerun · Pinocchio kinematics |
| Frontend | Vue 3 · Quasar · Vite · TypeScript · Tailwind · SPARK 2.0 + Three.js |
| QC tooling | FastAPI · Python · Seven quality filters · VLM task-completion evaluation |
| CLI & SDK | Python Click / Typer · S3 TransferManager · Lightweight edge upload SDK |

---

## Use Cases

**1 · Embodied AI startups** — Small algorithm teams, fast-growing data. They need a data pipeline they can adopt immediately so limited headcount stays on the model itself.

**2 · Universities and research labs** — Sensitive data, constrained budgets. They need local deployment and disciplined management to support long-running research and paper reproduction.

**3 · Autonomous driving teams** — Enormous multi-sensor time-series volumes requiring temporal alignment of point clouds and images, calibration-data management, and standard-format export.

**4 · Industrial robotics manufacturers** — Production-line operational data and failure samples needing classification and archival for anomaly detection and predictive-maintenance model training.

**5 · Data collection and annotation service providers** — Delivery quality is the core competitive edge. They need automated QC to replace manual first-pass screening, raising throughput and standardizing delivery.

**6 · Humanoid robot R&D teams** — High-frequency multimodal data, multi-view video, and proprioceptive state coexisting, with demanding requirements on time-synchronization precision and visual verification.

---

## The Value You Get

| Outcome | Target | Why it matters |
|---|---|---|
| **Order-of-magnitude efficiency gain** | Days → hours | Dataset preparation cycles compress sharply; algorithm iteration accelerates |
| **Annotation cost reduction** | −70% expected | Automated QC replaces manual first-pass screening; human effort goes where judgment is actually required |
| **Quantifiable data quality** | One standard | From intuition to scores — the team shares a common language for "is this data usable?" |
| **Lower training failure rate** | Blocked upfront | Bad data is intercepted before training, saving GPU hours |
| **Accumulating data assets** | Compounding value | Standardized domain datasets are reusable, appreciable long-term assets |
| **Controllable compliance risk** | Local deployment | Data never leaves the machine room; sensitive captures never touch external services |

> *Note: efficiency and cost figures are platform design targets. Actual results vary with data scale, hardware configuration, and business process. The deployed environment governs.*

---

## Deployment: Getting Started

**01 · Prepare the environment** — A server or workstation with a container runtime; plan disk capacity according to data scale.

**02 · One-command deployment** — Pull the images and run the unified startup script; all service components come up automatically.

**03 · Import data** — In the QC workbench, select a server path, drag and drop, or upload an archive for automatic extraction.

**04 · Run the pipeline** — Check the inspection items, run QC, review results, and export a clean dataset.

**Deployment options**

- **Private self-hosting** — On your own servers or on-premises bare metal. Data stays inside your enterprise boundary throughout — suited to teams with strict confidentiality requirements.
- **Private cloud** — In a virtual private network within your own cloud account, balancing elasticity and isolation, scaling with data volume.
- **Local workstation** — A single machine runs the complete QC flow, suited to individual researchers and small teams doing rapid validation and trials.

> No need to re-engineer your existing collection process. Put the data in, and the platform handles the rest.

---

## Extensibility: Ready Out of the Box, Room to Rebuild

**Full workflow in the UI** — No command line needed for daily work: import paths, check inspection items, run pipelines, view reports, replay in 3D, make human decisions, and export — all in the browser.

**Fully extensible code** — When you need custom rules, new formats, or extended interfaces, modify the frontend and backend code directly. No black box.

**Command-line toolchain** — A CLI lets you pull datasets directly on a training server, fitting neatly into automated training scripts.

**Open interfaces** — Core capabilities are exposed as interfaces, ready to integrate with existing R&D platforms, annotation systems, and training schedulers.

**Examples and templates** — Built-in example projects for data validation, metadata extraction, and format conversion serve as starting points for secondary development.

**Complete documentation** — Product documentation, user guides, API manuals, and operating guides are all in place, so new team members have a reference from day one.

> We don't build closed black boxes. What you get is a data foundation you can read, modify, and grow into your own business.

---

## Why Embodatahub: The Case for Replacing "File Share + Hand-Written Scripts"

| Dimension | The traditional way | Embodatahub |
|---|---|---|
| **Data organization** | Whole files, remembered by people, found by browsing directories | Four-tier model: Project → Mission → Episode → Streams |
| **Quality judgment** | A human plays back every video and judges by experience | Seven filters auto-score + VLM semantic evaluation |
| **Handling bad data** | It enters the training set; you find out when training crashes | Graded interception before training: passed / review / excluded |
| **Format adaptation** | A one-off conversion script per format | Five mainstream formats, bidirectional, with conversion reports |
| **Time synchronization** | Hand-written alignment scripts, no precision guarantee | Built-in temporal-sync detection with visual evidence |
| **Problem localization** | Guesswork and repeated trial and error | 3D replay + reporting dashboard + evidence frames |
| **Data security** | Uploaded to a third-party file share or public cloud | Local-first; data stays in your own machine room |
| **Team collaboration** | Shared directories and verbal handoffs | Permission system + task queue + open APIs |

---

## Roadmap

**Shipped — v1.0 core capabilities**
Dataset QC Workbench (seven filters + VLM evaluation), five-format bidirectional conversion, 3D replay and cleaning reports, data management platform, task queue and Worker scheduling, one-command deployment script.

**In progress — Stability and security hardening**
Identity authentication and permission-system refinement, large-file transfer reliability, service health checks and status monitoring, multi-environment configuration standardization, performance validation at real data scale.

**Coming soon — High availability and scale**
Distributed task scheduling, full-text metadata search, multi-storage backends with hot/cold tiering, unified alerting center, container cluster deployment suite, expanded operational dashboards.

**Planned — Ecosystem and industry customization**
Open API gateway with event callbacks, bidirectional integration with upstream and downstream systems, dataset versioning, industry-specific modules for autonomous driving and industrial robotics.

---

## Project Status

This platform was delivered as a commissioned project running July–September 2026. The following reflects the verified state at project close.

**Delivered subsystems**

| Component | Description |
|---|---|
| `backend` | NestJS API — users and permissions, project/mission/file metadata, API keys, templates, queue management |
| `frontend` | Vue 3 + Quasar main frontend — operational dashboard, data tables, project management, device status, bilingual |
| `robot-data-studio` | Dataset QC Workbench — LeRobot/HDF5/Zarr import and export, seven filters, VLM QC, Rerun replay |
| `spark-studio` | 3D scene visualization — SPARK 2.0 based 3DGS renderer and scene file browser |
| `queueConsumer` | Task queue service — asynchronous scheduling, worker heartbeat registration, preprocessing pipelines |
| `cli` / `world-model` | CLI tooling and model training — dataset pull tool; world-model training and VLA integration |

**Key performance indicators**

| Indicator | Target | Status at close |
|---|---|---|
| Large-file transfer reliability | > 99.9% success | S3 direct transfer / resumable upload implemented and functionally verified — *pending large-scale load test* |
| Multimodal timestamp alignment | < 5 ms error | Temporal-sync filter implemented in RDS and participating in scoring — *pending empirical calibration* |
| Data-cleaning automation rate | > 80% | Seven filters + VLM auto-scoring with passed/review/excluded grading — **capability delivered** |
| Dataset export cycle | Days → hours | Five mainstream formats, one-click export with conversion report — **capability delivered** |
| Concurrent edge terminals | 50+ | Queue and worker registration mechanisms in place, scheduling path verified — *pending concurrency load test* |
| Effective R&D time | + 30% | End-to-end automation in place — *pending post-launch data validation* |
| Manual annotation cost | −70% | Automated QC and auto-labeling replace manual first-pass screening — *pending post-launch data validation* |
| Model training convergence | + 20% | High-quality aligned-data supply path established — *pending training A/B validation* |

> Indicators marked *pending* require large-scale load testing, real-data regression, or training A/B comparison in a production environment before final figures can be confirmed. They are planned for observation during the first month after launch, with a jointly issued validation report.

---

## Contact

**Ningbo TsingtaoAI Intelligent Technology Co., Ltd.**
Room 203, Building B, Yonggang Modern Minglou
188 Jinghua Road, Juxian Street, High-tech Zone
Ningbo, Zhejiang, China

**What we can provide**

- Live product demonstration and a trial environment
- QC effectiveness validation on your own data
- Private deployment planning and capacity sizing
- Custom development and system integration support

---

*Embodatahub · Embodied Data Engineering Platform — Forge Robotic Intelligence*
