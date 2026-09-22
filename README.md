TsingtaoAI 中文定制版  
**⚠️ 重要说明：本项目是 Kleinkram 的中文定制版，并非官方原版，专为中文用户优化适配，与原版 Kleinkram 独立区分。**  
# **TsingtaoAI - 中文定制版机器人数据管理平台**  
TsingtaoAI 基于开源项目 Kleinkram 二次开发，是一款**全中文、可自托管**的机器人数据管理平台。我们保留了原版的核心功能，同时完成了全站汉化、Logo 定制，优化了中文用户的使用体验，解决了原版英文界面带来的操作门槛，让国内开发者、科研人员可快速上手使用。  
## **📌 与原版 Kleinkram 的核心区别**  
- **界面全中文**：全站菜单、按钮、表单、提示、文档均已汉化，彻底告别英文操作门槛，适配中文用户使用习惯。  
- **定制化标识**：替换原版 Logo，新增中文品牌标识，打造专属中文版本辨识度，与原版 Kleinkram 视觉区分。  
- **中文适配优化**：优化中文显示格式、字体适配，解决原版中文显示错乱、翻译生硬等问题。  
- **保留核心功能**：完全继承原版 Kleinkram 的所有核心能力，无功能删减，仅做中文适配和体验优化。  
- **独立分支维护**：基于原版 Kleinkram 构建独立分支 TsingtaoAI，独立开发、独立更新，不影响原版代码，也不会被原版更新覆盖。  
## **✨ 核心功能**  
继承原版核心能力，中文界面无缝衔接，主要功能包括：  
- **数据组织**：以「项目+任务」的结构，规范管理机器人相关数据，条理清晰。  
- **多格式存储**：支持 ROS 包（.bag、.mcap）、ZED 相机录制文件（.svo2）、配置文件（.yml）等机器人常用数据格式。  
- **自动化处理**：通过 TsingtaoAI 任务队列，实现数据验证、格式转换、内容提取等自动化操作。  
- **精细化权限控制**：支持用户组、角色管理，可 granular 分配数据访问权限，适合团队协作。  
- **可自托管**：支持本地部署、Docker 部署，数据完全私有，保障数据安全。  
## **🚀 快速开始（中文适配版）**  
本版本已优化中文部署流程，支持 Ubuntu 24.04、macOS 系统，Docker 一键部署，无需复杂配置。  
### **1. 克隆本项目（中文定制版）**  
git clone git@github.com:msd01580158/tsingtaoai.git  
cd tsingtaoai  
### **2. 启动应用（Docker 一键部署）**  
# 构建并启动所有服务，首次启动建议加上 --build 确保镜像同步  
docker compose up --build -d  
### **3. 访问平台**  
启动成功后，打开浏览器（推荐 Chrome/Firefox），访问以下地址即可进入全中文界面：  
http://localhost:8003  
### **4. 常见问题解决**  
若启动后出现「模块缺失」「API 无法访问」等问题，执行以下命令重建依赖并重启：  
docker compose rm -sf api-server queue-consumer frontend docs \  
&& docker volume rm kleinkram_backend_node_modules kleinkram_frontend_node_modules kleinkram_queue_consumer_node_modules kleinkram_node_modules \  
&& docker compose up -d --build api-server queue-consumer frontend docs  
## **📋 项目结构（中文说明）**  
tsingtaoai/  
├── backend          # 后端服务（中文错误提示适配）  
├── frontend         # 前端界面（全中文汉化、Logo 定制）  
├── docker           # Docker 部署配置（中文注释）  
├── docs             # 中文使用文档（待完善）  
├── queueConsumer    # 任务队列服务（功能不变，中文日志适配）  
└── docker-compose.yml # 一键部署配置（无需修改，直接使用）  
## **🔧 开发与更新**  
### **本地开发**  
# 进入前端目录，启动开发模式  
cd frontend  
pnpm dev  
   
# 进入后端目录，启动开发模式  
cd backend  
pnpm start:dev  
### **代码提交与更新**  
# 提交本地修改（中文提交说明）  
git add .  
git commit -m "feat: 新增中文文档/优化汉化"  
git push origin TsingtaoAI  
## **⚠️ 注意事项**  
- 本项目是 **TsingtaoAI 中文定制版**，与原版 Kleinkram（[https://github.com/leggedrobotics/kleinkram](https://github.com/leggedrobotics/kleinkram "https://github.com/leggedrobotics/kleinkram")）相互独立，更新、维护互不影响。  
- 若需要同步原版 Kleinkram 的最新功能，可手动合并原版 main 分支到本项目 TsingtaoAI 分支，合并后需重新检查汉化适配。  
- 部署时请确保 Docker、Docker Compose 已安装，建议使用 Ubuntu 24.04 系统以获得最佳兼容性。  
## **📞 反馈与贡献**  
若发现中文汉化不完整、界面显示异常、功能无法使用等问题，欢迎在本仓库提交 Issues 反馈。  
也欢迎各位开发者参与贡献，共同完善 TsingtaoAI 中文定制版，让更多中文用户受益。  
## **📄 许可证**  
继承原版 Kleinkram 的 LICENSE，保留 ETH 开源许可，详见项目根目录 LICENSE 文件。  
1. ✨ TsingtaoAI 中文定制版 | 基于 Kleinkram 开发，专为中文用户而生 ✨  
