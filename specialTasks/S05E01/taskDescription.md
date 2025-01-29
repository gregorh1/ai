# Phone Conversation Analysis Task

## Objective
Analyze transcribed phone conversations to identify inconsistencies, detect a liar among the speakers, and answer specific questions from Central Command.

## Input Files
1. `specialTasks/S05E01/resources/phone_sorted.json` - Transcribed conversations
2. `specialTasks/S05E01/resources/phone_questions.json` - Questions from Central Command
3. `specialTasks/S05E01/resources/*.txt` - Supporting facts from previous tasks

## Required Steps

### 1. Data Loading and Processing
- Load and parse conversations from `specialTasks/S05E01/resources/phone_sorted.json`
- Load questions from `specialTasks/S05E01/resources/phone_questions.json`
- Load supporting facts from `specialTasks/S05E01/resources/*.txt`

### 2. Conversation Analysis
- Identify unique speakers across all conversations
- Note: Each conversation involves exactly two people speaking alternately
- Note: If a name (e.g., Stefan) appears in multiple conversations, it's the same person

### 3. Truth Verification
- Cross-reference statements with:
   - Common knowledge
   - Facts from previous tasks
- Identify which speaker is providing false information

### 4. Answer Generation
- Process Central Command questions
- One question requires API interaction:
   - Fetch data from API
   - Process the response
   - Include it in the answers

### 5. Report Submission
- Submit results to: `https://centrala.ag3nts.org/report`
- Required JSON format:
```json
{
    "task": "phone",
    "apikey": "8b5c10c2-c4fd-4de4-816b-c465a365dbd0",
    "answer": {
        "01": "brief answer",
        "02": "brief answer",
        "03": "brief answer",
        "04": "brief answer",
        "05": "brief answer",
        "06": "brief answer"
    }
}
```

## Technical Notes
1. API key should be stored in `.env` file
2. Not all required information is directly provided in conversations
3. Some answers require cross-referencing with previous facts

## Implementation Approaches
### Minimal Version
- Focus on basic functionality
- Manual verification where needed
- Simple API interaction

### Advanced Version (Optional)
Create an autonomous system that can:
- Independently verify information
- Extract relevant facts
- Evaluate statement truthfulness
- Handle API communication
- Generate appropriate answers
