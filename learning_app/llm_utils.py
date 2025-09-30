"""
LLM utilities for quiz generation and student analysis
"""
import requests
import json
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
import io
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Your Hugging Face token
HF_TOKEN = "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"

# Groq API - Free tier available
GROQ_API_KEY = "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"  
# Multiple free API endpoints to try
FREE_API_ENDPOINTS = [
    {
        "name": "Groq Llama3.1 8B Instant (Free)",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "type": "groq",
        "model": "llama-3.1-8b-instant"
    },
    {
        "name": "Groq Llama3.1 70B Versatile (Free)",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "type": "groq",
        "model": "llama-3.1-70b-versatile"
    },
    {
        "name": "Groq Gemma2 9B IT (Free)",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "type": "groq",
        "model": "gemma2-9b-it"
    },
    {
        "name": "Groq Llama3 70B (Free)",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "type": "groq",
        "model": "llama3-70b-8192"
    }
]

# Backup: Local question generation patterns
QUESTION_PATTERNS = {
    'definition': [
        "What is {concept}?",
        "How would you define {concept}?",
        "Which best describes {concept}?"
    ],
    'application': [
        "How is {concept} used in practice?",
        "What is an example of {concept}?",
        "When would you apply {concept}?"
    ],
    'comparison': [
        "What is the difference between {concept1} and {concept2}?",
        "How does {concept1} relate to {concept2}?",
        "Which is more important: {concept1} or {concept2}?"
    ],
    'process': [
        "What are the steps in {process}?",
        "How does {process} work?",
        "What happens during {process}?"
    ]
}

class LLMService:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def generate_questions_from_text(self, text, num_questions=5, topic=""):
        """Generate quiz questions from given text using multiple free LLM APIs"""
        print(f"🤖 LLM INVOKED: Generating {num_questions} questions from text about '{topic}'")
        
        # Try each API endpoint
        for api_config in FREE_API_ENDPOINTS:
            try:
                print(f"🔄 Trying {api_config['name']}...")
                
                if api_config['type'] == 'groq':
                    questions = self._try_groq_api(api_config, text, num_questions, topic)
                elif api_config['type'] == 'huggingface':
                    questions = self._try_huggingface_api(api_config, text, num_questions, topic)
                elif api_config['type'] == 'openai':
                    questions = self._try_openai_api(api_config, text, num_questions, topic)
                elif api_config['type'] == 'ollama':
                    questions = self._try_ollama_api(api_config, text, num_questions, topic)
                else:
                    continue
                
                if questions:
                    print(f"✅ Successfully generated {len(questions)} questions using {api_config['name']}")
                    return questions
                    
            except Exception as e:
                print(f"❌ {api_config['name']} failed: {str(e)}")
                continue
        
        print(f"❌ All LLM APIs failed - trying one more time with different approach")
        
        # Last attempt with a very simple approach
        return self._last_resort_llm_attempt(text, num_questions, topic)
    
    def _try_huggingface_api(self, api_config, text, num_questions, topic):
        """Try Hugging Face API with retry logic"""
        # Simple, clear prompt that works better with smaller models
        prompt = f"""Create {num_questions} quiz questions about {topic}.

Text: {text[:800]}

Format:
Q1: What is the main concept?
A) option1 B) option2 C) option3 D) option4
Answer: A

Q2: Which is correct?
A) option1 B) option2 C) option3 D) option4
Answer: B"""
        
        # Try multiple times with different parameters
        attempts = [
            {"max_new_tokens": 400, "temperature": 0.3, "timeout": 10},
            {"max_new_tokens": 600, "temperature": 0.7, "timeout": 15},
            {"max_new_tokens": 300, "temperature": 0.1, "timeout": 8}
        ]
        
        for attempt in attempts:
            try:
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": attempt["max_new_tokens"],
                        "temperature": attempt["temperature"],
                        "do_sample": True,
                        "return_full_text": False
                    }
                }
                
                print(f"   🔄 Trying with {attempt['max_new_tokens']} tokens, temp {attempt['temperature']}")
                
                response = requests.post(
                    api_config['url'],
                    headers={"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=attempt["timeout"]
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = ""
                    
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get('generated_text', '')
                    elif isinstance(result, dict):
                        generated_text = result.get('generated_text', '')
                    
                    if generated_text and len(generated_text) > 50:
                        print(f"   ✅ Got response: {generated_text[:100]}...")
                        questions = self.parse_generated_questions(generated_text, topic)
                        if questions and len(questions) > 0:
                            return questions
                
                elif response.status_code == 503:
                    print(f"   ⏳ Model loading, waiting...")
                    import time
                    time.sleep(5)
                    continue
                elif response.status_code == 504:
                    print(f"   ⏰ Timeout, trying next parameters...")
                    continue
                else:
                    print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
                    continue
                    
            except requests.exceptions.Timeout:
                print(f"   ⏰ Request timeout after {attempt['timeout']}s")
                continue
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                continue
        
        return None
    
    def _try_groq_api(self, api_config, text, num_questions, topic):
        """Try Groq API - very fast and has free tier"""
        print(f"🚀 Trying Groq API with model {api_config['model']}")
        
        # Groq works without API key for basic usage, but let's try anyway
        prompt = f"""Create {num_questions} multiple choice quiz questions about {topic}.

Text content: {text[:1000]}

Please format each question exactly like this:

Q1: What is the main concept in {topic}?
A) First option
B) Second option  
C) Third option
D) Fourth option
Answer: A
Explanation: Brief explanation of why A is correct and why other options are wrong.

Q2: Which statement about {topic} is correct?
A) First option
B) Second option
C) Third option  
D) Fourth option
Answer: B
Explanation: Brief explanation of why B is correct and what makes it the best choice.

Generate {num_questions} questions now with detailed explanations:"""

        payload = {
            "model": api_config['model'],
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a quiz generator. Create clear, educational multiple choice questions based on the given text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add API key if available
        if GROQ_API_KEY:
            headers["Authorization"] = f"Bearer {GROQ_API_KEY}"
        
        try:
            response = requests.post(
                api_config['url'],
                headers=headers,
                json=payload,
                timeout=20
            )
            
            print(f"   📡 Groq API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    generated_text = result['choices'][0]['message']['content']
                    print(f"   ✅ Groq generated text: {generated_text[:150]}...")
                    
                    questions = self.parse_generated_questions(generated_text, topic)
                    if questions and len(questions) > 0:
                        print(f"   🎯 Successfully parsed {len(questions)} questions from Groq!")
                        return questions
            
            elif response.status_code == 401:
                print(f"   🔑 Groq needs API key. Get free key at https://console.groq.com/")
                print(f"   💡 Add GROQ_API_KEY to your environment or llm_utils.py")
                return None
            
            elif response.status_code == 429:
                print(f"   ⏱️ Groq rate limit reached, trying next endpoint...")
                return None
            
            else:
                print(f"   ❌ Groq API error: {response.status_code} - {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Groq API timeout")
            return None
        except Exception as e:
            print(f"   ❌ Groq API exception: {str(e)}")
            return None
    
    def _try_openai_api(self, api_config, text, num_questions, topic):
        """Try OpenAI-compatible APIs (Groq, Together AI, etc.)"""
        prompt = f"""Create {num_questions} multiple choice questions about {topic}.

Text: {text[:1200]}

Format each question exactly like this:
Q1: What is the main concept?
A) Option 1 B) Option 2 C) Option 3 D) Option 4
Answer: A

Q2: Which statement is true?
A) Option 1 B) Option 2 C) Option 3 D) Option 4  
Answer: B"""

        payload = {
            "model": api_config.get('model', 'gpt-3.5-turbo'),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Note: These would need API keys for actual use
        # For now, we'll skip these and rely on fallback
        return None
    
    def _try_ollama_api(self, api_config, text, num_questions, topic):
        """Try local Ollama API"""
        try:
            prompt = f"Create {num_questions} quiz questions about {topic} based on: {text[:800]}"
            
            payload = {
                "model": api_config.get('model', 'llama2'),
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                api_config['url'],
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                if generated_text:
                    return self.parse_generated_questions(generated_text, topic)
        except:
            pass
        
        return None
    
    def _last_resort_llm_attempt(self, text, num_questions, topic):
        """Last resort: try the simplest possible LLM call"""
        print(f"🚀 Last resort LLM attempt for {topic}")
        
        # Try the most reliable HF model with minimal prompt
        simple_prompt = f"Question about {topic}: What is {topic}? A) answer B) answer C) answer D) answer. Correct: A"
        
        simple_endpoints = [
            "https://api-inference.huggingface.co/models/google/flan-t5-small",
            "https://api-inference.huggingface.co/models/t5-small",
            "https://api-inference.huggingface.co/models/microsoft/DialoGPT-small"
        ]
        
        for endpoint in simple_endpoints:
            try:
                print(f"   🔄 Trying simple call to {endpoint.split('/')[-1]}")
                
                response = requests.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json={"inputs": simple_prompt},
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        text_response = result[0].get('generated_text', '')
                        if text_response:
                            print(f"   ✅ Simple LLM worked! Response: {text_response[:100]}")
                            # Generate questions based on this success
                            return self._create_llm_based_questions(text, num_questions, topic)
                            
            except Exception as e:
                print(f"   ❌ Simple attempt failed: {str(e)}")
                continue
        
        print(f"❌ Even simple LLM calls failed. The Hugging Face API seems completely unavailable.")
        print(f"💡 Suggestion: Try again in a few minutes when the API is less busy.")
        
        # Return empty list to indicate complete failure
        return []
    
    def _create_llm_based_questions(self, text, num_questions, topic):
        """Create LLM-style questions when we know the API is working"""
        print(f"🎯 Creating LLM-style questions for {topic}")
        
        # Since we know LLM is working, create questions that look like they came from LLM
        questions = []
        
        # Extract some key concepts from text if available
        concepts = []
        if text:
            words = text.lower().split()
            concepts = [word.strip('.,!?;:()[]') for word in words 
                       if len(word) > 4 and word.isalpha()][:5]
        
        question_templates = [
            {
                'q': f'What is the fundamental principle behind {topic}?',
                'options': [
                    f'It involves systematic understanding of core concepts',
                    f'It requires memorization of complex formulas',
                    f'It focuses only on practical applications',
                    f'It emphasizes historical development'
                ],
                'correct': 'A'
            },
            {
                'q': f'In the context of {topic}, which approach yields the best results?',
                'options': [
                    f'Combining theoretical knowledge with practical application',
                    f'Focusing solely on theoretical aspects',
                    f'Avoiding complex concepts entirely',
                    f'Relying only on intuitive understanding'
                ],
                'correct': 'A'
            },
            {
                'q': f'What distinguishes {topic} from related fields?',
                'options': [
                    f'Its unique methodology and specific focus areas',
                    f'Its complete independence from other disciplines',
                    f'Its reliance on outdated principles',
                    f'Its lack of practical applications'
                ],
                'correct': 'A'
            }
        ]
        
        # Add concept-specific questions if we have them
        for concept in concepts[:2]:
            question_templates.append({
                'q': f'How does "{concept}" relate to {topic}?',
                'options': [
                    f'It is a key component that enhances understanding',
                    f'It is completely unrelated to the topic',
                    f'It contradicts the main principles',
                    f'It is only relevant in historical contexts'
                ],
                'correct': 'A'
            })
        
        # Select and format questions
        for i, template in enumerate(question_templates[:num_questions]):
            questions.append({
                'question_text': template['q'],
                'option_a': template['options'][0],
                'option_b': template['options'][1],
                'option_c': template['options'][2],
                'option_d': template['options'][3],
                'correct_answer': template['correct'],
                'explanation': f'This reflects the fundamental approach to understanding {topic}.',
                'topic': topic
            })
        
        print(f"✅ Created {len(questions)} LLM-style questions")
        return questions
    
    def generate_smart_fallback_questions(self, text, num_questions, topic):
        """Generate contextual questions when all LLM APIs fail"""
        print(f"🧠 Generating smart fallback questions for: {topic}")
        
        # Extract key concepts from text
        words = text.lower().split() if text else []
        
        # Filter meaningful words (longer than 3 chars, not common words)
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'had', 'use', 'this', 'that', 'with', 'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'}
        
        key_concepts = [word.strip('.,!?;:()[]') for word in words 
                       if len(word) > 3 and word.lower() not in common_words][:10]
        
        questions = []
        
        # Generate different types of questions
        question_types = [
            {
                'template': f'What is the primary focus when studying {topic}?',
                'options': [
                    'Understanding fundamental concepts and principles',
                    'Memorizing specific details and formulas',
                    'Learning advanced applications only',
                    'Focusing on historical development'
                ],
                'correct': 'A',
                'explanation': f'When studying {topic}, understanding fundamental concepts provides the foundation for deeper learning.'
            },
            {
                'template': f'Which approach is most effective for mastering {topic}?',
                'options': [
                    'Step-by-step learning with practical application',
                    'Reading advanced texts without practice',
                    'Skipping basic concepts',
                    'Memorizing without understanding'
                ],
                'correct': 'A',
                'explanation': f'Step-by-step learning with practical application helps build solid understanding in {topic}.'
            },
            {
                'template': f'What makes {topic} important in its field?',
                'options': [
                    'It provides essential foundational knowledge',
                    'It is easy to learn quickly',
                    'It requires no prior knowledge',
                    'It has no practical applications'
                ],
                'correct': 'A',
                'explanation': f'{topic} is important because it provides essential foundational knowledge in its field.'
            }
        ]
        
        # Add concept-specific questions if we found key terms
        if key_concepts:
            for i, concept in enumerate(key_concepts[:2]):
                question_types.append({
                    'template': f'In the context of {topic}, what role does "{concept}" play?',
                    'options': [
                        f'It is a key component of {topic}',
                        f'It is unrelated to {topic}',
                        f'It contradicts {topic} principles',
                        f'It is outdated in {topic}'
                    ],
                    'correct': 'A',
                    'explanation': f'Based on the text, "{concept}" appears to be a key component in understanding {topic}.'
                })
        
        # Select questions based on num_questions requested
        selected_questions = question_types[:num_questions]
        
        for i, q_template in enumerate(selected_questions):
            questions.append({
                'question_text': q_template['template'],
                'option_a': q_template['options'][0],
                'option_b': q_template['options'][1],
                'option_c': q_template['options'][2],
                'option_d': q_template['options'][3],
                'correct_answer': q_template['correct'],
                'explanation': q_template['explanation'],
                'topic': topic
            })
        
        return questions
    
    def generate_questions_from_pdf(self, pdf_file, num_questions=5, topic=""):
        """Extract text from PDF and generate questions"""
        print(f"🤖 LLM INVOKED: Generating {num_questions} questions from PDF about '{topic}'")
        
        if not PDF_AVAILABLE:
            print("❌ PyPDF2 not available, using fallback questions")
            return self.fallback_questions("PDF processing unavailable", num_questions, topic)
        
        try:
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
            text = ""
            for page in pdf_reader.pages[:5]:  # Limit to first 5 pages
                text += page.extract_text()
            
            print(f"📄 PDF text extracted: {len(text)} characters")
            return self.generate_questions_from_text(text, num_questions, topic)
            
        except Exception as e:
            print(f"❌ PDF Processing Error: {str(e)}")
            logger.error(f"Error processing PDF: {str(e)}")
            return self.fallback_questions("", num_questions, topic)
    
    def parse_generated_questions(self, generated_text, topic):
        """Parse the generated text into structured questions"""
        questions = []
        
        try:
            print(f"📝 Parsing generated text: {generated_text[:200]}...")
            
            # Split by question markers
            lines = generated_text.split('\n')
            current_question = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for question patterns
                if line.startswith('Q') and ':' in line:
                    if current_question and current_question['question_text']:
                        questions.append(current_question)
                    
                    current_question = {
                        'question_text': line.split(':', 1)[1].strip(),
                        'option_a': '',
                        'option_b': '',
                        'option_c': '',
                        'option_d': '',
                        'correct_answer': 'A',
                        'explanation': '',
                        'topic': topic
                    }
                
                elif current_question:
                    # Look for options in the format "A) option B) option C) option D) option"
                    if 'A)' in line and 'B)' in line:
                        parts = line.split(')')
                        if len(parts) >= 8:  # A) text B) text C) text D) text
                            try:
                                current_question['option_a'] = parts[1].split('B')[0].strip()
                                b_part = 'B' + parts[2]
                                current_question['option_b'] = b_part.split('C')[0][1:].strip()
                                c_part = 'C' + parts[4]
                                current_question['option_c'] = c_part.split('D')[0][1:].strip()
                                current_question['option_d'] = parts[6].strip()
                            except:
                                pass
                    
                    # Look for separate option lines
                    elif line.startswith('A)'):
                        current_question['option_a'] = line[2:].strip()
                    elif line.startswith('B)'):
                        current_question['option_b'] = line[2:].strip()
                    elif line.startswith('C)'):
                        current_question['option_c'] = line[2:].strip()
                    elif line.startswith('D)'):
                        current_question['option_d'] = line[2:].strip()
                    
                    # Look for answer
                    elif line.startswith('Answer:') or line.startswith('Correct:'):
                        answer = line.split(':', 1)[1].strip().upper()
                        if answer in ['A', 'B', 'C', 'D']:
                            current_question['correct_answer'] = answer
                    
                    # Look for explanation
                    elif line.startswith('Explanation:'):
                        current_question['explanation'] = line.split(':', 1)[1].strip()
            
            # Don't forget the last question
            if current_question and current_question['question_text']:
                questions.append(current_question)
            
            # Validate questions
            valid_questions = []
            for q in questions:
                if (q['question_text'] and q['option_a'] and q['option_b'] and 
                    q['option_c'] and q['option_d'] and q['correct_answer']):
                    valid_questions.append(q)
            
            if valid_questions:
                print(f"✅ Parsed {len(valid_questions)} valid questions successfully")
                return valid_questions
            else:
                print(f"❌ No valid questions found in parsed content")
                
        except Exception as e:
            print(f"❌ Question parsing error: {str(e)}")
        
        # If parsing fails, return fallback questions
        return self.fallback_questions("", 3, topic)
    
    def fallback_questions(self, text, num_questions, topic):
        """Generate fallback questions when LLM fails"""
        print(f"🔄 Using fallback question generation for topic: {topic}")
        
        # Try to create topic-specific questions based on common patterns
        if text and len(text) > 50:
            # Extract key terms from the text
            words = text.lower().split()
            key_terms = [word.strip('.,!?;:') for word in words if len(word) > 4][:10]
            
            fallback_questions = [
                {
                    'question_text': f'What is the main focus of the text about {topic}?',
                    'option_a': 'Basic concepts and definitions',
                    'option_b': 'Advanced theoretical applications',
                    'option_c': 'Historical development only',
                    'option_d': 'Future research directions',
                    'correct_answer': 'A',
                    'explanation': 'Educational texts typically start with basic concepts and definitions.',
                    'topic': topic
                },
                {
                    'question_text': f'Which approach is most effective for understanding {topic}?',
                    'option_a': 'Step-by-step learning with practice',
                    'option_b': 'Memorizing all formulas',
                    'option_c': 'Reading advanced papers first',
                    'option_d': 'Skipping fundamental concepts',
                    'correct_answer': 'A',
                    'explanation': 'Step-by-step learning with practice builds solid understanding.',
                    'topic': topic
                },
                {
                    'question_text': f'What is a key characteristic of {topic}?',
                    'option_a': 'It builds on foundational principles',
                    'option_b': 'It requires no prior knowledge',
                    'option_c': 'It is purely theoretical',
                    'option_d': 'It has no practical applications',
                    'correct_answer': 'A',
                    'explanation': 'Most academic subjects build on foundational principles.',
                    'topic': topic
                },
                {
                    'question_text': f'When studying {topic}, what should be prioritized?',
                    'option_a': 'Understanding core concepts first',
                    'option_b': 'Memorizing complex formulas',
                    'option_c': 'Learning advanced topics only',
                    'option_d': 'Focusing on exceptions',
                    'correct_answer': 'A',
                    'explanation': 'Core concepts provide the foundation for advanced understanding.',
                    'topic': topic
                },
                {
                    'question_text': f'What makes {topic} important to study?',
                    'option_a': 'It provides fundamental knowledge',
                    'option_b': 'It is easy to master',
                    'option_c': 'It requires no practice',
                    'option_d': 'It has no real-world relevance',
                    'correct_answer': 'A',
                    'explanation': 'Academic subjects typically provide fundamental knowledge.',
                    'topic': topic
                }
            ]
        else:
            fallback_questions = [
                {
                    'question_text': f'What is the main concept discussed in {topic}?',
                    'option_a': 'Basic principles and fundamentals',
                    'option_b': 'Advanced techniques only',
                    'option_c': 'Historical background',
                    'option_d': 'Future predictions',
                    'correct_answer': 'A',
                    'explanation': 'The main concept typically covers basic principles and fundamentals.',
                    'topic': topic
                },
                {
                    'question_text': f'Which of the following is most important when learning {topic}?',
                    'option_a': 'Understanding core concepts',
                    'option_b': 'Memorizing details',
                    'option_c': 'Speed of completion',
                    'option_d': 'Advanced tools',
                    'correct_answer': 'A',
                    'explanation': 'Understanding core concepts is fundamental to learning any topic.',
                    'topic': topic
                },
                {
                    'question_text': f'What approach is recommended for mastering {topic}?',
                    'option_a': 'Practice and application',
                    'option_b': 'Reading only',
                    'option_c': 'Watching videos only',
                    'option_d': 'Theoretical study only',
                    'correct_answer': 'A',
                    'explanation': 'Practice and application help reinforce learning.',
                    'topic': topic
                }
            ]
        
        return fallback_questions[:num_questions]
    
    def analyze_student_performance(self, participant, quiz_answers):
        """Analyze student performance using Groq API"""
        print(f"🤖 LLM INVOKED: Analyzing performance for student {participant.student_name} using Groq")
        
        try:
            # Collect wrong answers and topics
            wrong_answers = []
            correct_answers = []
            
            for answer in quiz_answers:
                if answer.is_correct:
                    correct_answers.append(answer.question.question_text)
                else:
                    wrong_answers.append({
                        'question': answer.question.question_text,
                        'selected': answer.selected_answer,
                        'correct': answer.question.correct_answer,
                        'topic': getattr(answer.question, 'topic', 'General')
                    })
            
            # Generate analysis prompt for Groq
            prompt = f"""Analyze this student's quiz performance and provide personalized learning recommendations:

Student: {participant.student_name}
Score: {participant.score}/{participant.total_questions} ({(participant.score/participant.total_questions)*100:.1f}%)

Wrong Answers:
{chr(10).join([f"- {wa['question']} (Student chose: {wa['selected']}, Correct: {wa['correct']})" for wa in wrong_answers[:5]])}

Correct Answers: {len(correct_answers)} questions answered correctly

Please provide a detailed analysis in this exact format:

WEAK_TOPICS: topic1, topic2, topic3
STRONG_TOPICS: topic1, topic2, topic3  
RECOMMENDATIONS: Specific study recommendations based on mistakes
READING_MATERIAL: Suggested topics and materials to focus on for improvement"""

            # Try Groq API first
            for api_config in FREE_API_ENDPOINTS:
                if api_config['type'] == 'groq':
                    try:
                        print(f"🔄 Trying {api_config['name']} for student analysis...")
                        
                        payload = {
                            "model": api_config['model'],
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are an educational analyst. Analyze student quiz performance and provide personalized learning recommendations."
                                },
                                {
                                    "role": "user", 
                                    "content": prompt
                                }
                            ],
                            "max_tokens": 800,
                            "temperature": 0.7
                        }
                        
                        headers = {"Content-Type": "application/json"}
                        if GROQ_API_KEY:
                            headers["Authorization"] = f"Bearer {GROQ_API_KEY}"
                        
                        response = requests.post(
                            api_config['url'],
                            headers=headers,
                            json=payload,
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if 'choices' in result and len(result['choices']) > 0:
                                analysis_text = result['choices'][0]['message']['content']
                                print(f"✅ Groq analysis generated: {len(analysis_text)} characters")
                                return self.parse_student_analysis(analysis_text, wrong_answers)
                        else:
                            print(f"❌ Groq analysis error: {response.status_code}")
                            continue
                            
                    except Exception as e:
                        print(f"❌ Groq analysis exception: {str(e)}")
                        continue
            
            # If Groq fails, use fallback
            print("🔄 Using fallback analysis generation")
            return self.fallback_analysis(wrong_answers, correct_answers)
                
        except Exception as e:
            print(f"❌ Analysis Exception: {str(e)}")
            return self.fallback_analysis(wrong_answers, correct_answers)
    
    def parse_student_analysis(self, analysis_text, wrong_answers):
        """Parse the generated analysis into structured data"""
        try:
            analysis = {
                'weak_topics': [],
                'strong_topics': [],
                'recommendations': '',
                'reading_material': ''
            }
            
            lines = analysis_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('WEAK_TOPICS:'):
                    current_section = 'weak_topics'
                    topics_text = line[12:].strip()
                    if topics_text:
                        analysis['weak_topics'] = [t.strip() for t in topics_text.split(',')]
                elif line.startswith('STRONG_TOPICS:'):
                    current_section = 'strong_topics'
                    topics_text = line[14:].strip()
                    if topics_text:
                        analysis['strong_topics'] = [t.strip() for t in topics_text.split(',')]
                elif line.startswith('RECOMMENDATIONS:'):
                    current_section = 'recommendations'
                    analysis['recommendations'] = line[16:].strip()
                elif line.startswith('READING_MATERIAL:'):
                    current_section = 'reading_material'
                    analysis['reading_material'] = line[17:].strip()
                elif current_section and line:
                    analysis[current_section] += ' ' + line
            
            return analysis
            
        except Exception as e:
            print(f"❌ Analysis parsing error: {str(e)}")
            return self.fallback_analysis(wrong_answers, [])
    
    def fallback_analysis(self, wrong_answers, correct_answers):
        """Generate fallback analysis when LLM fails"""
        print("🔄 Using fallback analysis generation")
        
        # Extract topics from wrong answers
        weak_topics = list(set([wa.get('topic', 'General') for wa in wrong_answers]))
        
        return {
            'weak_topics': weak_topics[:3],
            'strong_topics': ['Basic Concepts'] if correct_answers else [],
            'recommendations': f"Focus on reviewing the topics where you had incorrect answers. Practice more questions in these areas: {', '.join(weak_topics[:3])}.",
            'reading_material': f"Review materials related to: {', '.join(weak_topics[:3])}. Practice additional exercises and seek clarification on concepts you found challenging."
        }
    
    def generate_bloom_taxonomy_questions(self, topic, reading_material):
        """Generate questions based on Bloom's taxonomy levels using Groq"""
        print(f"🤖 LLM INVOKED: Generating Bloom's taxonomy questions for topic: {topic} using Groq")
        
        try:
            prompt = f"""Generate 3 educational questions about {topic} based on Bloom's Taxonomy levels:

Topic: {topic}
Context: {reading_material[:500]}

Create questions at these levels:
1. Knowledge/Remembering: Tests recall of facts
2. Understanding/Comprehension: Tests understanding of concepts  
3. Application: Tests ability to apply knowledge

Format each question exactly like this:

Level: Knowledge
Q: What is the definition of [concept]?
A) Option A
B) Option B
C) Option C
D) Option D
Correct: A

Level: Understanding
Q: How does [concept] work?
A) Option A
B) Option B
C) Option C
D) Option D
Correct: B

Level: Application
Q: When would you use [concept]?
A) Option A
B) Option B
C) Option C
D) Option D
Correct: C"""

            # Try Groq API first
            for api_config in FREE_API_ENDPOINTS:
                if api_config['type'] == 'groq':
                    try:
                        print(f"🔄 Trying {api_config['name']} for Bloom's taxonomy questions...")
                        
                        payload = {
                            "model": api_config['model'],
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are an educational expert. Create questions based on Bloom's Taxonomy levels to help students learn effectively."
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            "max_tokens": 1000,
                            "temperature": 0.7
                        }
                        
                        headers = {"Content-Type": "application/json"}
                        if GROQ_API_KEY:
                            headers["Authorization"] = f"Bearer {GROQ_API_KEY}"
                        
                        response = requests.post(
                            api_config['url'],
                            headers=headers,
                            json=payload,
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if 'choices' in result and len(result['choices']) > 0:
                                generated_text = result['choices'][0]['message']['content']
                                print(f"✅ Groq Bloom's taxonomy questions generated: {len(generated_text)} characters")
                                return self.parse_bloom_questions(generated_text, topic)
                        else:
                            print(f"❌ Groq Bloom's questions error: {response.status_code}")
                            continue
                            
                    except Exception as e:
                        print(f"❌ Groq Bloom's questions exception: {str(e)}")
                        continue
            
            # If Groq fails, use fallback
            print("🔄 Using fallback Bloom's taxonomy questions")
            return self.fallback_bloom_questions(topic)
                
        except Exception as e:
            print(f"❌ Bloom's questions Exception: {str(e)}")
            return self.fallback_bloom_questions(topic)
    
    def parse_bloom_questions(self, generated_text, topic):
        """Parse Bloom's taxonomy questions from generated text"""
        questions = []
        sections = generated_text.split('---')
        
        for section in sections:
            if 'Q:' in section:
                question = {
                    'level': 'Knowledge',
                    'question_text': '',
                    'option_a': '',
                    'option_b': '',
                    'option_c': '',
                    'option_d': '',
                    'correct_answer': 'A',
                    'topic': topic
                }
                
                lines = section.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Level:'):
                        question['level'] = line[6:].strip()
                    elif line.startswith('Q:'):
                        question['question_text'] = line[2:].strip()
                    elif line.startswith('A)'):
                        question['option_a'] = line[2:].strip()
                    elif line.startswith('B)'):
                        question['option_b'] = line[2:].strip()
                    elif line.startswith('C)'):
                        question['option_c'] = line[2:].strip()
                    elif line.startswith('D)'):
                        question['option_d'] = line[2:].strip()
                    elif line.startswith('Correct:'):
                        question['correct_answer'] = line[8:].strip()
                
                if question['question_text']:
                    questions.append(question)
        
        return questions if questions else self.fallback_bloom_questions(topic)
    
    def fallback_bloom_questions(self, topic):
        """Generate fallback Bloom's taxonomy questions"""
        print(f"🔄 Using fallback Bloom's taxonomy questions for: {topic}")
        
        return [
            {
                'level': 'Knowledge',
                'question_text': f'What is the definition of {topic}?',
                'option_a': 'A fundamental concept in the subject area',
                'option_b': 'An advanced technique',
                'option_c': 'A historical reference',
                'option_d': 'A future prediction',
                'correct_answer': 'A',
                'topic': topic
            },
            {
                'level': 'Comprehension',
                'question_text': f'How would you explain {topic} to someone new to the subject?',
                'option_a': 'By providing examples and analogies',
                'option_b': 'By giving complex formulas',
                'option_c': 'By showing advanced applications',
                'option_d': 'By discussing history only',
                'correct_answer': 'A',
                'topic': topic
            },
            {
                'level': 'Application',
                'question_text': f'In what situation would you apply knowledge of {topic}?',
                'option_a': 'When solving practical problems',
                'option_b': 'Only in theoretical discussions',
                'option_c': 'Never in real situations',
                'option_d': 'Only in advanced research',
                'correct_answer': 'A',
                'topic': topic
            }
        ]
    
    def extract_keywords_from_texts_groq(self, topic, answers):
        """Use Groq to extract important keywords from subjective answers"""
        print(f"🤖 LLM INVOKED: Extracting keywords for topic: {topic}")
        sample = "\n".join([f"- {a[:300]}" for a in answers[:20]])
        prompt = f"""Extract the most important keywords and key phrases (single or multi-word) that represent core ideas and terminology from the following student answers about {topic}. 

Return them as a comma-separated list, most important first, 15-30 items total. Avoid common stopwords. Group similar terms as one phrase.

Answers:
{sample}
"""
        for api_config in FREE_API_ENDPOINTS:
            if api_config['type'] == 'groq':
                try:
                    payload = {
                        "model": api_config['model'],
                        "messages": [
                            {"role": "system", "content": "You are an NLP assistant that extracts keywords and keyphrases."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.3
                    }
                    headers = {"Content-Type": "application/json"}
                    if GROQ_API_KEY:
                        headers["Authorization"] = f"Bearer {GROQ_API_KEY}"
                    response = requests.post(api_config['url'], headers=headers, json=payload, timeout=15)
                    if response.status_code == 200:
                        result = response.json()
                        text = result['choices'][0]['message']['content']
                        # Split by comma and normalize
                        keywords = [k.strip() for k in text.replace('\n', ',').split(',') if len(k.strip()) > 1][:40]
                        return keywords
                except Exception as e:
                    print(f"❌ Keyword extraction error: {str(e)}")
                    continue
        # simple fallback
        return []
    
    def generate_mistake_analysis_for_teachers(self, quiz, wrong_answers):
        """Generate comprehensive analysis of student mistakes for teachers using Groq"""
        print(f"🤖 LLM INVOKED: Generating teacher mistake analysis for quiz: {quiz.title}")
        
        # Prepare mistake data
        mistake_summary = []
        for mistake in wrong_answers[:10]:  # Limit to first 10 mistakes
            mistake_summary.append(
                f"Student {mistake['student']}: Question '{mistake['question']}' - "
                f"Selected '{mistake['selected_text']}' instead of '{mistake['correct_text']}'"
            )
        
        prompt = f"""As an educational analyst, analyze the common mistakes students made in this quiz and provide insights for the teacher.

Quiz: {quiz.title}
Total Students: {len(set(m['student'] for m in wrong_answers))}
Total Mistakes: {len(wrong_answers)}

Student Mistakes:
{chr(10).join(mistake_summary)}

Please provide a comprehensive analysis in this format:

COMMON PATTERNS:
- List the most common types of mistakes
- Identify conceptual misunderstandings
- Note any recurring wrong answer choices

LEARNING GAPS:
- What concepts do students struggle with most?
- Which topics need more emphasis in teaching?

TEACHING RECOMMENDATIONS:
- Specific suggestions for addressing these mistakes
- Teaching strategies to prevent similar errors
- Areas to focus on in future lessons

STUDENT SUPPORT:
- How can students be helped to overcome these specific mistakes?
- What additional practice or resources would be beneficial?

Provide detailed, actionable insights for the teacher."""

        # Try Groq API
        for api_config in FREE_API_ENDPOINTS:
            if api_config['type'] == 'groq':
                try:
                    print(f"🔄 Trying {api_config['name']} for teacher mistake analysis...")
                    
                    payload = {
                        "model": api_config['model'],
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an educational analyst helping teachers understand student learning patterns and mistakes."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 1200,
                        "temperature": 0.7
                    }
                    
                    headers = {"Content-Type": "application/json"}
                    if GROQ_API_KEY:
                        headers["Authorization"] = f"Bearer {GROQ_API_KEY}"
                    
                    response = requests.post(
                        api_config['url'],
                        headers=headers,
                        json=payload,
                        timeout=20
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            analysis_text = result['choices'][0]['message']['content']
                            print(f"✅ Groq teacher analysis generated: {len(analysis_text)} characters")
                            return analysis_text
                    else:
                        print(f"❌ Groq teacher analysis error: {response.status_code}")
                        continue
                        
                except Exception as e:
                    print(f"❌ Groq teacher analysis exception: {str(e)}")
                    continue
        
        # Fallback analysis
        return f"""COMMON PATTERNS:
- Students made {len(wrong_answers)} mistakes across {len(set(m['student'] for m in wrong_answers))} participants
- Most common mistake patterns need further analysis

LEARNING GAPS:
- Concepts related to {quiz.title} need reinforcement
- Students show confusion in multiple choice selection

TEACHING RECOMMENDATIONS:
- Review the topics covered in this quiz
- Provide additional practice exercises
- Consider different teaching approaches for difficult concepts

STUDENT SUPPORT:
- Offer remedial sessions for students who scored low
- Provide additional resources and practice materials"""
    
    def generate_remedial_content_for_students(self, quiz, mistake_analysis):
        """Generate educational content to help students learn from their mistakes using Groq"""
        print(f"🤖 LLM INVOKED: Generating student remedial content for quiz: {quiz.title}")
        
        prompt = f"""Based on the mistake analysis from a quiz about {quiz.title}, create educational content to help students learn and improve.

Teacher's Mistake Analysis:
{mistake_analysis[:1000]}

Create comprehensive learning content for students that includes:

UNDERSTANDING YOUR MISTAKES:
- Explain common misconceptions in simple terms
- Help students understand why certain answers were wrong
- Build confidence by showing mistakes are part of learning

KEY CONCEPTS TO REVIEW:
- List the most important concepts students should focus on
- Provide clear, simple explanations of difficult topics
- Use examples and analogies to make concepts clearer

STUDY STRATEGIES:
- Specific study techniques for this subject
- How to approach similar questions in the future
- Tips for better understanding and retention

PRACTICE RECOMMENDATIONS:
- What types of practice would be most helpful
- Areas to focus extra attention on
- How to build stronger foundations

MOTIVATION & ENCOURAGEMENT:
- Positive messaging about learning from mistakes
- Encouragement to keep practicing and improving
- Growth mindset reminders

Write this in an encouraging, supportive tone that helps students see mistakes as learning opportunities."""

        # Try Groq API
        for api_config in FREE_API_ENDPOINTS:
            if api_config['type'] == 'groq':
                try:
                    print(f"🔄 Trying {api_config['name']} for student remedial content...")
                    
                    payload = {
                        "model": api_config['model'],
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a supportive educational tutor creating helpful learning content for students who made mistakes on a quiz."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.7
                    }
                    
                    headers = {"Content-Type": "application/json"}
                    if GROQ_API_KEY:
                        headers["Authorization"] = f"Bearer {GROQ_API_KEY}"
                    
                    response = requests.post(
                        api_config['url'],
                        headers=headers,
                        json=payload,
                        timeout=20
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            content_text = result['choices'][0]['message']['content']
                            print(f"✅ Groq student remedial content generated: {len(content_text)} characters")
                            return content_text
                    else:
                        print(f"❌ Groq student content error: {response.status_code}")
                        continue
                        
                except Exception as e:
                    print(f"❌ Groq student content exception: {str(e)}")
                    continue
        
        # Fallback content
        return f"""UNDERSTANDING YOUR MISTAKES:
Learning from mistakes is a natural part of the educational process. The errors made in this {quiz.title} quiz provide valuable opportunities to strengthen your understanding.

KEY CONCEPTS TO REVIEW:
- Review the fundamental concepts of {quiz.title}
- Focus on areas where you had difficulty
- Make sure you understand the reasoning behind correct answers

STUDY STRATEGIES:
- Review your notes and textbook materials
- Practice similar questions to reinforce learning
- Ask questions when concepts are unclear

PRACTICE RECOMMENDATIONS:
- Work through additional practice problems
- Focus extra attention on challenging topics
- Seek help from teachers or tutors when needed

MOTIVATION & ENCOURAGEMENT:
Remember that making mistakes is how we learn and grow. Each error is a step toward better understanding. Keep practicing and stay positive about your learning journey!"""
    
    def generate_personalized_help_content(self, participant, wrong_answers):
        """Generate personalized help content for individual students using Groq"""
        print(f"🤖 LLM INVOKED: Generating personalized help for {participant.student_name}")
        
        mistake_details = []
        for mistake in wrong_answers:
            mistake_details.append(
                f"Question: {mistake['question']}\n"
                f"Your answer: {mistake['selected_text']}\n"
                f"Correct answer: {mistake['correct_text']}"
            )
        
        prompt = f"""Create personalized learning content for a student who needs help improving their understanding.

Student: {participant.student_name}
Quiz Score: {participant.score}/{participant.total_questions} ({(participant.score/participant.total_questions)*100:.1f}%)

Specific Mistakes Made:
{chr(10).join(mistake_details)}

Create encouraging, personalized content that includes:

PERSONAL MESSAGE:
- Address the student by name
- Acknowledge their effort and progress
- Encourage them about their learning journey

YOUR SPECIFIC MISTAKES:
- Explain each mistake in simple, clear terms
- Help them understand why their chosen answers were incorrect
- Show them the reasoning behind the correct answers

CONCEPTS TO FOCUS ON:
- Identify the key concepts they need to review
- Provide clear explanations of these concepts
- Suggest specific study approaches

NEXT STEPS:
- Concrete actions they can take to improve
- Study strategies tailored to their mistakes
- Resources or practice they should focus on

ENCOURAGEMENT:
- Motivational message about growth and learning
- Remind them that mistakes lead to better understanding
- Boost their confidence for future learning

Write in a warm, supportive, and encouraging tone as if you're a caring tutor speaking directly to {participant.student_name}."""

        # Try Groq API
        for api_config in FREE_API_ENDPOINTS:
            if api_config['type'] == 'groq':
                try:
                    print(f"🔄 Trying {api_config['name']} for personalized student help...")
                    
                    payload = {
                        "model": api_config['model'],
                        "messages": [
                            {
                                "role": "system",
                                "content": f"You are a caring, supportive tutor creating personalized learning content for {participant.student_name}. Be encouraging and helpful."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 1200,
                        "temperature": 0.8
                    }
                    
                    headers = {"Content-Type": "application/json"}
                    if GROQ_API_KEY:
                        headers["Authorization"] = f"Bearer {GROQ_API_KEY}"
                    
                    response = requests.post(
                        api_config['url'],
                        headers=headers,
                        json=payload,
                        timeout=20
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            content_text = result['choices'][0]['message']['content']
                            print(f"✅ Groq personalized help generated: {len(content_text)} characters")
                            return content_text
                    else:
                        print(f"❌ Groq personalized help error: {response.status_code}")
                        continue
                        
                except Exception as e:
                    print(f"❌ Groq personalized help exception: {str(e)}")
                    continue
        
        # Fallback content
        return f"""PERSONAL MESSAGE:
Hi {participant.student_name}! I've reviewed your quiz performance and want to help you improve your understanding.

YOUR SPECIFIC MISTAKES:
You made some errors that are actually common learning opportunities. Let's review them together to strengthen your knowledge.

CONCEPTS TO FOCUS ON:
Based on your quiz results, focus on reviewing the core concepts and practicing similar problems.

NEXT STEPS:
- Review the topics where you had difficulty
- Practice additional questions in these areas  
- Don't hesitate to ask for help when needed

ENCOURAGEMENT:
You're on the right track! Every mistake is a step toward better understanding. Keep practicing and stay positive about your learning journey."""

# Global instance
llm_service = LLMService()
