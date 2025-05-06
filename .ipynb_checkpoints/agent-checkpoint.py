{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "0aaa0038-43b6-4f96-bc51-ee4f1e7bbecb",
   "metadata": {},
   "outputs": [],
   "source": [
    "import openai\n",
    "import re\n",
    "import httpx\n",
    "import os\n",
    "from dotenv import load_dotenv\n",
    "\n",
    "_ = load_dotenv()\n",
    "from openai import OpenAI"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "46979db6-df94-4709-b012-cd21ab5ad59e",
   "metadata": {},
   "outputs": [],
   "source": [
    "client = OpenAI()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "69818868-8797-411b-a02d-67bdd267c7ff",
   "metadata": {},
   "outputs": [],
   "source": [
    "chat_completion = client.chat.completions.create(\n",
    "    model=\"gpt-3.5-turbo\",\n",
    "    messages=[{\"role\": \"user\", \"content\": \"hi\"}]\n",
    ")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "1ec6efcb-593e-4bad-b94f-8764253a8e58",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "'Hello! How can I assist you today?'"
      ]
     },
     "execution_count": 4,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "chat_completion.choices[0].message.content"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "id": "117d9278-de26-4f79-a774-4bdc08280880",
   "metadata": {},
   "outputs": [],
   "source": [
    "class Agent:\n",
    "    def __init__(self, system=\"\"):\n",
    "        self.system = system\n",
    "        self.messages = []\n",
    "        if self.system:\n",
    "            self.messages.append({\"role\": \"system\", \"content\": system})\n",
    "\n",
    "    def __call__(self, message):\n",
    "        self.messages.append({\"role\": \"user\", \"content\": message})\n",
    "        result = self.execute()\n",
    "        self.messages.append({\"role\": \"assistant\", \"content\": result})\n",
    "        return result\n",
    "\n",
    "    def execute(self):\n",
    "        completion = client.chat.completions.create(\n",
    "                        model=\"gpt-4o\", \n",
    "                        temperature=0,\n",
    "                        messages=self.messages)\n",
    "        return completion.choices[0].message.content\n",
    "    "
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 17,
   "id": "eef25eb3-0a35-4c24-a844-84b8935dea11",
   "metadata": {},
   "outputs": [],
   "source": [
    "prompt = \"\"\"\n",
    "You are a Currency Conversion Assistant. You reason in a loop of Thought → Action → PAUSE → Observation, and when done you output an Answer.\n",
    "\n",
    "Use Thought to explain your plan.  \n",
    "Use Action to call one of these tools, then immediately output PAUSE.  \n",
    "After you receive an Observation, continue the loop or output your final Answer.\n",
    "\n",
    "Available actions:\n",
    "  convert_currency: <amount> <from_currency> to <to_currency>\n",
    "    – Fetches the latest exchange rate and returns the converted amount.\n",
    "  calculate: <arithmetic_expression>\n",
    "    – Evaluates a numeric expression using Python.\n",
    "\n",
    "Format requirements:\n",
    "  • Every step must start with “Thought:”, “Action:”, “PAUSE”, or “Observation:”.  \n",
    "  • Final response must start with “Answer:”.  \n",
    "  • Do not include any extra text outside these labels.\n",
    "\n",
    "Example 1:\n",
    "Question: Convert 100 USD to EUR.\n",
    "Thought: I need the current USD→EUR exchange rate.\n",
    "Action: convert_currency: 100 USD to EUR\n",
    "PAUSE\n",
    "\n",
    "(Then, after your code runs…)\n",
    "\n",
    "You will be called again with this:\n",
    "Observation: 84.35 EUR\n",
    "\n",
    "Then you output :\n",
    "Answer: 100 USD equals approximately 84.35 EUR.\n",
    "\n",
    "Example 2:\n",
    "Question: What is the value of (250 GBP → JPY) plus 1000 JPY in GBP?\n",
    "Thought: First convert 250 GBP to JPY.\n",
    "Action: convert_currency: 250 GBP to JPY\n",
    "PAUSE\n",
    "You will be called again with this:\n",
    "Observation: 38,500 JPY\n",
    "Then you output :\n",
    "Action: convert_currency: 1000 JPY to GBP\n",
    "PAUSE\n",
    "\n",
    "You will be called again with this:\n",
    "Observation: 1.85 GBP\n",
    "Then you output :\n",
    "Action: calculate: 250 + 1.85\n",
    "PAUSE\n",
    "\n",
    "You will be called again with this:\n",
    "Observation: 251.85\n",
    "Then you output :\n",
    "Answer: The total is 251.85 GBP.\n",
    "\"\"\"\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 20,
   "id": "19c4adc3-26a8-46f6-b8d1-c03b4d7fdc75",
   "metadata": {},
   "outputs": [],
   "source": [
    "import re\n",
    "\n",
    "# Dummy exchange rates for testing without API calls\n",
    "DUMMY_RATES = {\n",
    "    ('USD', 'EUR'): 0.88,\n",
    "    ('EUR', 'USD'): 1.14,\n",
    "    ('USD', 'JPY'): 110.0,\n",
    "    ('JPY', 'USD'): 0.0091,\n",
    "    ('GBP', 'USD'): 1.25,\n",
    "    ('USD', 'GBP'): 0.80,\n",
    "}\n",
    "\n",
    "def convert_currency(cmd):\n",
    "    \"\"\"\n",
    "    Dummy convert_currency implementation.\n",
    "    cmd format: \"<amount> <from> to <to>\"\n",
    "    \"\"\"\n",
    "    try:\n",
    "        parts = cmd.split()\n",
    "        amt = float(parts[0])\n",
    "        frm = parts[1]\n",
    "        to = parts[3]\n",
    "    except Exception:\n",
    "        return \"Invalid format. Use: <amount> <from> to <to>\"\n",
    "    rate = DUMMY_RATES.get((frm, to))\n",
    "    if rate is None:\n",
    "        return f\"Rate for {frm}→{to} not found in dummy rates.\"\n",
    "    converted = amt * rate\n",
    "    return f\"{converted:.2f} {to}\"\n",
    "\n",
    "def calculate(expr):\n",
    "    \"\"\"Evaluate a numeric expression using Python.\"\"\"\n",
    "    try:\n",
    "        result = eval(expr, {}, {})\n",
    "        return str(result)\n",
    "    except Exception as e:\n",
    "        return f\"Calculation error: {e}\"\n",
    "\n",
    "known_actions = {\n",
    "    \"convert_currency\": convert_currency,\n",
    "    \"calculate\": calculate,\n",
    "}  \n",
    "\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "a1cdffe4-c96a-4b0f-a5e3-33403835572e",
   "metadata": {},
   "outputs": [],
   "source": []
  },
  {
   "cell_type": "code",
   "execution_count": 21,
   "id": "053b6c3e-9a63-4208-8930-37d88944b989",
   "metadata": {},
   "outputs": [],
   "source": [
    "action_re = re.compile('^Action: (\\w+): (.*)$')   # python regular expression to selection action"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 22,
   "id": "3d855f45-891c-44ea-aa37-737f85787595",
   "metadata": {},
   "outputs": [],
   "source": [
    "def query(question, max_turns=5):\n",
    "    i = 0\n",
    "    bot = Agent(prompt)\n",
    "    next_prompt = question\n",
    "    while i < max_turns:\n",
    "        i += 1\n",
    "        result = bot(next_prompt)\n",
    "        print(result)\n",
    "        actions = [\n",
    "            action_re.match(a) \n",
    "            for a in result.split('\\n') \n",
    "            if action_re.match(a)\n",
    "        ]\n",
    "        if actions:\n",
    "            # There is an action to run\n",
    "            action, action_input = actions[0].groups()\n",
    "            if action not in known_actions:\n",
    "                raise Exception(\"Unknown action: {}: {}\".format(action, action_input))\n",
    "            print(\" -- running {} {}\".format(action, action_input))\n",
    "            observation = known_actions[action](action_input)\n",
    "            print(\"Observation:\", observation)\n",
    "            next_prompt = \"Observation: {}\".format(observation)\n",
    "        else:\n",
    "            return"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 25,
   "id": "8c3d2892-90c0-44f4-8f22-c9267796206f",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Thought: First, I need to convert 20 USD to JPY.\n",
      "Action: convert_currency: 20 USD to JPY\n",
      "PAUSE\n",
      " -- running convert_currency 20 USD to JPY\n",
      "Observation: 2200.00 JPY\n",
      "Thought: Now, I need to convert 10 JPY to USD.\n",
      "Action: convert_currency: 10 JPY to USD\n",
      "PAUSE\n",
      " -- running convert_currency 10 JPY to USD\n",
      "Observation: 0.09 USD\n",
      "Thought: I have the results of both conversions. Now, I need to add 2200 JPY and 0.09 USD, but first, I should convert 0.09 USD to JPY to perform the addition in the same currency.\n",
      "Action: convert_currency: 0.09 USD to JPY\n",
      "PAUSE\n",
      " -- running convert_currency 0.09 USD to JPY\n",
      "Observation: 9.90 JPY\n",
      "Thought: Now I can add 2200 JPY and 9.90 JPY together.\n",
      "Action: calculate: 2200 + 9.90\n",
      "PAUSE\n",
      " -- running calculate 2200 + 9.90\n",
      "Observation: 2209.9\n",
      "Answer: The total is 2209.9 JPY.\n"
     ]
    }
   ],
   "source": [
    "question = \"\"\"What is (20 USD → JPY) plus (10 JPY → USD)?\"\"\"\n",
    "query(question)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "5970bbdb-0678-4e15-8aa5-e8efe1180069",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python (venv)",
   "language": "python",
   "name": "venv"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.11"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
