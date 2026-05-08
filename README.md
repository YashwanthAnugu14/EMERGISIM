# 🚨 EmergiSim — Event Simulation & Risk Analysis System

<div align="center">

![](https://img.shields.io/badge/Python-Simulation_System-3776AB?style=for-the-badge&logo=python&logoColor=white)
![](https://img.shields.io/badge/Streamlit-Interactive_UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge)
![](https://img.shields.io/badge/Risk-Analytics-FF8C00?style=for-the-badge)

</div>

---

# 👨‍💻 Developed By

### Yashwanth Reddy Anugu

---

# 📂 File Name

### `emergisim.py`

---

# 🚀 About This Project

EmergiSim is a simulation-based web application designed to model complex event-driven systems where uncertainty, risk, and dependencies play a major role in decision making.

In many real-world situations such as emergency planning, workflow management, IT incident response, and operational analysis, events do not happen independently. One event can affect multiple other events, creating chains of dependencies and risks that are difficult to track manually.

To address this problem, I developed EmergiSim. The system allows users to create events, define relationships between them, run probabilistic simulations, and analyze different possible outcomes using interactive visualizations and analytics.

The application combines simulation logic, dependency validation, conflict detection, risk analysis, and reporting into a single platform that is easy to use and highly interactive.

---

# ❗ Problem Statement

Traditional workflow and planning systems usually focus only on fixed execution paths and predictable scenarios. However, in real-world systems:

- Events often contain uncertainty
- Risks can propagate across dependencies
- Conflicts may occur between execution chains
- Failure in one event can impact many others
- Manual analysis becomes difficult for large systems

Most existing tools lack proper simulation capabilities and fail to provide clear visualization of event relationships and risks.

EmergiSim solves these problems by:

- Simulating multiple event outcomes
- Modeling dependency relationships
- Detecting conflicts automatically
- Calculating risk impact dynamically
- Providing interactive visual analytics

---

# 🎯 System Objectives

- Model event-driven systems effectively
- Simulate uncertain execution scenarios
- Analyze event dependencies and relationships
- Detect conflicts and invalid structures
- Visualize risk and execution patterns
- Improve planning and decision support
- Support multiple user roles securely

---

# ✨ Key Features

# 🧩 Event Management

- Create new events
- Update event information
- Delete existing events
- Clone events quickly
- Assign duration, probability, and priority
- Define event failure risk values

---

# 🔗 Dependency Modeling

- Create relationships between events
- Define execution order constraints
- Validate dependency structures
- Prevent circular dependency creation
- Analyze connected event chains

---

# ⚡ Simulation Engine

- Generate multiple event execution scenarios
- Apply probabilistic simulation logic
- Support dependency-aware execution
- Simulate uncertain system behavior
- Evaluate different possible outcomes

---

# ⚠️ Conflict Detection

- Detect circular dependencies
- Identify missing event references
- Detect priority conflicts
- Highlight high-risk execution chains
- Validate event consistency automatically

---

# 📊 Analytics & Visualization

The system provides several advanced visual outputs including:

- Dependency Graph Visualization
- Risk Distribution Histogram
- Radar Chart Analysis
- Gantt Timeline Visualization
- 3D Risk Surface
- Bubble Chart for Risk vs Likelihood

These visual components help users better understand system behavior, risks, and event relationships.

---

# 👥 User Management

### 🛡️ Administrator
- Full system access
- Manage users and permissions
- Configure system settings

### 📅 Planner
- Create and organize event plans
- Define dependencies and workflows

### 📈 Analyst
- Run simulations and analyze results
- Review risk and conflict reports

### 👁️ Observer
- Read-only access
- Monitor simulation outputs and analytics

---

# 📁 Data Import & Export

- Import event data using JSON and CSV
- Export simulation outputs
- Support structured data management
- Simplify external data integration

---

# 📝 Reporting

- Generate structured simulation reports
- Display execution summaries
- Present conflict analysis
- Provide visual analytical outputs

---

# ⚙️ Technologies Used

<div align="center">

![](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge)
![](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)

</div>

### Technologies Included

- Python for backend simulation logic
- Streamlit for interactive UI development
- SQLite for lightweight database storage
- Pandas for structured data analysis
- NumPy for numerical operations
- Matplotlib for charts and visualizations
- NetworkX for dependency graph processing

---

# 🏗️ Project Structure

```plaintext
EmergiSim/
│
├── emergisim.py
├── emergisim.db
├── README.md
└── requirements.txt
```

---

# ⚙️ Installation

## 📥 Clone Repository

```bash
git clone https://github.com/your-username/emergisim.git
cd emergisim
```

---

## 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Application

```bash
streamlit run emergisim.py
```

After running the command, open the generated local URL in your browser to access the application.

---

# 🔐 Default Login Credentials

## 🛡️ Administrator
- Username: `admin`
- Password: `admin123`

## 📅 Planner
- Username: `planner`
- Password: `demo123`

## 📈 Analyst
- Username: `analyst`
- Password: `analyst123`

## 👁️ Observer
- Username: `observer`
- Password: `observer123`

---

# 🔄 System Workflow

### 1️⃣ Event Creation
Users create events with attributes such as duration, execution probability, priority, and failure risk.

### 2️⃣ Dependency Definition
Relationships between events are configured to model real-world constraints and execution order.

### 3️⃣ Simulation Execution
The system generates multiple possible execution paths using probabilistic simulation logic.

### 4️⃣ Conflict Analysis
The application validates dependencies and detects structural or execution conflicts automatically.

### 5️⃣ Risk Evaluation
Risk scores and event impact levels are calculated dynamically.

### 6️⃣ Visualization & Reporting
Users analyze outputs using charts, graphs, dashboards, and reports.

---

# 📊 Outputs Generated

The system generates multiple analytical outputs including:

- Dependency Graph Visualization
- Gantt Timeline Chart
- Risk Radar Analysis
- Risk Distribution Histogram
- 3D Risk Surface Visualization
- Bubble Chart for Risk vs Likelihood
- Simulation Result Reports
- Conflict Detection Reports

---

# 🌍 Real-World Use Cases

### 🚑 Emergency Response Planning
Model and simulate emergency workflows and response chains.

### 💻 IT Incident Simulation
Analyze infrastructure failures and cascading impacts.

### ⚙️ Workflow Optimization
Study dependency bottlenecks and execution efficiency.

### 📈 Risk Analysis
Evaluate uncertainty and event propagation risks.

### 🎓 Training & Decision Support
Support educational simulations and planning exercises.

---

# 🧠 Design Approach

While building this project, I mainly focused on:

- Creating an interactive and visually rich interface
- Supporting realistic simulation behavior
- Maintaining modular system architecture
- Ensuring dependency validation accuracy
- Simplifying user interaction and navigation
- Providing meaningful visual analytics

Even though the application is lightweight and easy to run, the architecture is designed in a scalable and extensible manner for future improvements.

---

# 📌 Important Notes

- The system uses probabilistic simulation, so outputs may vary between runs
- Circular dependencies are automatically validated and restricted
- The database is generated automatically during first execution
- Visual analytics update dynamically based on simulation results

---

# ⚠️ Current Limitations

- SQLite is not ideal for high-scale concurrent usage
- No cloud synchronization support currently
- Real-time collaboration is not available
- AI-based prediction models are not yet integrated

---

# 🚀 Future Improvements

- Real-time collaborative simulation support
- AI-powered predictive risk analysis
- Cloud deployment integration
- External API connectivity
- Advanced reporting dashboards
- Machine learning based event forecasting
- Distributed simulation support

---

# 🧪 Testing

The application includes testing support for:

- Event creation and validation
- Dependency relationship checks
- Circular dependency detection
- Simulation execution logic
- Risk calculation mechanisms
- User role management
- Reporting functionality

---

# 🌟 Conclusion

EmergiSim provides a powerful and interactive platform for understanding event-driven systems with uncertainty and dependencies.

Instead of relying on static workflows or manual analysis, the system enables users to simulate multiple execution possibilities, evaluate risks, detect conflicts, and visualize outcomes clearly.

The project demonstrates how simulation, dependency analysis, and visualization can improve planning, decision making, and operational awareness in complex environments.
