# **Technical Challenge: The Intelligent Data Room**

**Role:** GenAI & Full Stack Engineering Intern **Duration:** 48 Hours

## **1\. The Goal**

Build a small web application that allows users to upload a CSV file and "talk" to their data. Instead of a simple chatbot, you must implement a **Multi-Agent System** where tasks are split between "Thinking" and "Doing."

## **2\. Functional Requirements**

* **Data Upload:** Support for CSV/XLSX files (Max 10MB).  
* **The Multi-Agent Workflow:**  
  * **Agent 1 (The Planner):** Analyzes the user's natural language question and the data schema. It outputs a step-by-step "Execution Plan."  
  * **Agent 2 (The Executor):** Uses **PandasAI** (and the Google Gemini API) to execute the plan, write the Python code, and retrieve the answer.  
* **Visualization:** If the user asks for a trend or comparison, the app should automatically render a chart (using Plotly, Recharts, or Matplotlib).  
* **Context Retention:** The system must remember the last 3-5 messages to handle follow-up questions (e.g., User: "Who are the top 5 customers?" \-\> User: "Now show their locations on a map.").

## **3\. Technical Stack**

* **Backend/AI:** Python, PandasAI, Google Gemini API (Recommended).  
* **Frontend/UI:** Streamlit (for speed) OR React/TypeScript .  
* **Hosting:** GitHub (Code) \+ Streamlit Cloud/Vercel (Live Link).

## **4\. Sample Dataset & Testing**

* **Dataset:** Please use the [Sample Sales Dataset (CSV)](https://drive.google.com/file/d/1na63aBcSPm2q3-t1TxUlO9lMKElmr_YY/view?usp=sharing) for your internal testing.

## **5\. Deliverables**

1. **Public GitHub Repository:** Include a `README.md` with setup instructions.  
2. **Live Application Link  (Optional but highly encouraged):** A URL where we can test the app immediately.  
3. **Short Video:**  A 2-minute Loom/Screen-record explaining how your agents communicate and how you handled context/memory.

## **6\. Evaluation Criteria**

* **System Prompting:** How well did you define the roles of your agents?  
* **Code Quality:** Is your code modular, commented, and typed?  
* **User Experience (UX):** Is the chat interface clean? Are the charts easy to read?  
* **Reasoning:** Can you explain *why* the agent chose a specific plan?

## 7\. Sample Prompts

### **Easy Prompts**

1. **Prompt:** Create a bar chart showing the total **Sales** and **Profit** for each **Category**.  
2. **Prompt:** Visualize the distribution of total **Sales** across different **Regions** using a pie chart.  
3. **Prompt:** Which **Customer Segment** places the most orders? Show this with a count plot.  
4. **Prompt:** Identify the **Top 5 States** by total Sales using a horizontal bar chart.  
5. **Prompt:** How has the total **Profit** changed over the **Years** (2018–2021)? Use a line chart.

---

### **Medium Prompts**

6. **Prompt:** Which **Sub-Categories** are currently unprofitable on average? Visualize this with a bar chart.  
7. **Prompt:** Compare the **Sales Trend** of different **Ship Modes** over time using a multi-line chart. \-   
8. **Prompt:** List the **Top 10 Customers** by total Profit and display them in a bar chart.  
9. **Prompt:** Is there a correlation between **Discount** and **Profit**? Create a scatter plot to show the relationship.  
10. **Prompt:** Calculate and chart the **Return Rate** (percentage of orders returned) for each **Region**.

