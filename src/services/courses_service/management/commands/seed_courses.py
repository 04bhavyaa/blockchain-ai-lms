"""
Management command to seed sample courses into the database
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from src.services.courses_service.models import (
    Course, CourseCategory, Module, Lesson, Quiz, Question, Answer
)

User = get_user_model()

SAMPLE_COURSES = [
    {
        'title': 'Introduction to Blockchain Technology',
        'slug': 'introduction-to-blockchain',
        'description': 'Learn the fundamentals of blockchain technology, including how it works, key concepts, and real-world applications. This course covers everything from basic cryptography to smart contracts.',
        'category': 'Blockchain',
        'difficulty_level': 'beginner',
        'duration_hours': 20,
        'access_type': 'free',
        'token_cost': 0,
        'tags': ['blockchain', 'cryptocurrency', 'web3', 'beginners'],
        'learning_objectives': [
            'Understand core blockchain concepts',
            'Learn about consensus mechanisms',
            'Explore smart contracts',
            'Understand cryptocurrency basics'
        ],
        'is_featured': True,
        'modules': [
            {
                'title': 'Blockchain Fundamentals',
                'description': 'Core concepts of blockchain technology',
                'lessons': [
                    {
                        'title': 'What is Blockchain?',
                        'description': 'Introduction to distributed ledger technology',
                        'content_url': 'https://www.youtube.com/embed/SSo_EIwHSd4',
                        'content_type': 'video',
                        'duration_minutes': 15,
                        'is_free_preview': True,
                        'transcript': 'Blockchain is a distributed ledger technology that maintains a continuously growing list of records, called blocks, which are linked and secured using cryptography.',
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Blockchain Basics Quiz',
                            'description': 'Test your understanding of blockchain fundamentals',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What is a blockchain?',
                                    'explanation': 'A blockchain is a distributed ledger that maintains records in blocks linked by cryptography.',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'A centralized database', 'is_correct': False},
                                        {'text': 'A distributed ledger technology', 'is_correct': True},
                                        {'text': 'A type of cryptocurrency', 'is_correct': False},
                                        {'text': 'A cloud storage system', 'is_correct': False},
                                    ]
                                },
                                {
                                    'question_type': 'true_false',
                                    'text': 'Blockchain transactions are irreversible once confirmed.',
                                    'explanation': 'Yes, once a transaction is confirmed and added to the blockchain, it becomes permanent.',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'True', 'is_correct': True},
                                        {'text': 'False', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                    {
                        'title': 'Blockchain Architecture',
                        'description': 'Understanding blocks, chains, and nodes',
                        'content_url': 'https://www.youtube.com/embed/Yn8WGaO__ak',
                        'content_type': 'video',
                        'duration_minutes': 20,
                        'transcript': 'Blockchain architecture consists of blocks containing transactions, connected in a chain. Each node maintains a copy of the entire blockchain.',
                    },
                    {
                        'title': 'Consensus Mechanisms',
                        'description': 'Proof of Work vs Proof of Stake',
                        'content_url': 'https://www.youtube.com/embed/3EUAcx7o6d8',
                        'content_type': 'video',
                        'duration_minutes': 25,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Consensus Mechanisms Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'Which consensus mechanism does Bitcoin use?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'Proof of Stake', 'is_correct': False},
                                        {'text': 'Proof of Work', 'is_correct': True},
                                        {'text': 'Proof of Authority', 'is_correct': False},
                                        {'text': 'Delegated Proof of Stake', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                ]
            },
            {
                'title': 'Cryptocurrency Basics',
                'description': 'Introduction to digital currencies',
                'lessons': [
                    {
                        'title': 'Introduction to Bitcoin',
                        'description': 'The first cryptocurrency and how it works',
                        'content_url': 'https://www.youtube.com/embed/bBC-nXj3Ng4',
                        'content_type': 'video',
                        'duration_minutes': 18,
                        'is_free_preview': True,
                        'transcript': 'Bitcoin was created in 2009 as the first decentralized cryptocurrency. It uses blockchain technology to enable peer-to-peer transactions without intermediaries.',
                    },
                    {
                        'title': 'How Bitcoin Mining Works',
                        'description': 'Understanding the mining process and rewards',
                        'content_url': 'https://www.youtube.com/embed/bBC-nXj3Ng4',
                        'content_type': 'video',
                        'duration_minutes': 25,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Bitcoin Mining Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What is Bitcoin mining?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'Creating new Bitcoins', 'is_correct': False},
                                        {'text': 'Validating transactions and creating blocks', 'is_correct': True},
                                        {'text': 'Selling Bitcoins', 'is_correct': False},
                                        {'text': 'Storing Bitcoins', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                    {
                        'title': 'Ethereum and Smart Contracts',
                        'description': 'Programmable blockchain and decentralized applications',
                        'content_url': 'https://www.youtube.com/embed/jxLkbJozK3Y',
                        'content_type': 'video',
                        'duration_minutes': 22,
                        'transcript': 'Ethereum extends blockchain technology beyond currency, enabling smart contracts and decentralized applications (dApps).',
                    },
                    {
                        'title': 'Wallets and Private Keys',
                        'description': 'Understanding cryptocurrency wallets and security',
                        'content_url': 'https://www.youtube.com/embed/bBC-nXj3Ng4',
                        'content_type': 'video',
                        'duration_minutes': 20,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Wallets and Security Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'true_false',
                                    'text': 'You should share your private key with others.',
                                    'explanation': 'Never share your private key! It gives full access to your wallet.',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'True', 'is_correct': False},
                                        {'text': 'False', 'is_correct': True},
                                    ]
                                },
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What is a hardware wallet?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'A physical device that stores private keys offline', 'is_correct': True},
                                        {'text': 'A software application', 'is_correct': False},
                                        {'text': 'An online service', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                ]
            },
            {
                'title': 'Blockchain Applications',
                'description': 'Real-world uses of blockchain technology',
                'lessons': [
                    {
                        'title': 'Supply Chain Management',
                        'description': 'How blockchain improves supply chain transparency',
                        'content_url': 'https://www.youtube.com/embed/SSo_EIwHSd4',
                        'content_type': 'video',
                        'duration_minutes': 22,
                    },
                    {
                        'title': 'Digital Identity',
                        'description': 'Blockchain-based identity solutions',
                        'content_url': 'https://www.youtube.com/embed/SSo_EIwHSd4',
                        'content_type': 'video',
                        'duration_minutes': 18,
                    },
                ]
            }
        ]
    },
    {
        'title': 'Advanced Smart Contract Development',
        'slug': 'advanced-smart-contracts',
        'description': 'Master Solidity programming and build production-ready smart contracts. Learn about security best practices, gas optimization, and DeFi protocols.',
        'category': 'Blockchain',
        'difficulty_level': 'advanced',
        'duration_hours': 40,
        'access_type': 'token',
        'token_cost': 50,
        'tags': ['solidity', 'smart-contracts', 'defi', 'ethereum'],
        'learning_objectives': [
            'Master Solidity programming',
            'Build secure smart contracts',
            'Understand gas optimization',
            'Create DeFi applications'
        ],
        'is_featured': True,
        'modules': [
                    {
                        'title': 'Solidity Fundamentals',
                        'description': 'Learn the Solidity programming language',
                        'lessons': [
                            {
                                'title': 'Solidity Syntax',
                                'description': 'Learn the Solidity programming language',
                                'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                                'content_type': 'video',
                                'duration_minutes': 30,
                                'has_quiz': True,
                                'quiz': {
                                    'title': 'Solidity Syntax Quiz',
                                    'passing_score': 70,
                                    'questions': [
                                        {
                                            'question_type': 'multiple_choice',
                                            'text': 'What is the main language for Ethereum smart contracts?',
                                            'points': 1,
                                            'answers': [
                                                {'text': 'JavaScript', 'is_correct': False},
                                                {'text': 'Solidity', 'is_correct': True},
                                                {'text': 'Python', 'is_correct': False},
                                                {'text': 'Go', 'is_correct': False},
                                            ]
                                        },
                                    ]
                                }
                            },
                            {
                                'title': 'Contract Structure',
                                'description': 'Understanding contracts, functions, and variables',
                                'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                                'content_type': 'video',
                                'duration_minutes': 25,
                                'transcript': 'Solidity contracts contain state variables, functions, events, and modifiers. Understanding the structure is crucial for smart contract development.',
                            },
                            {
                                'title': 'Data Types and Variables',
                                'description': 'Solidity data types and variable declarations',
                                'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                                'content_type': 'video',
                                'duration_minutes': 28,
                                'has_quiz': True,
                                'quiz': {
                                    'title': 'Data Types Quiz',
                                    'passing_score': 70,
                                    'questions': [
                                        {
                                            'question_type': 'multiple_choice',
                                            'text': 'Which is NOT a valid Solidity data type?',
                                            'points': 1,
                                            'answers': [
                                                {'text': 'uint256', 'is_correct': False},
                                                {'text': 'string', 'is_correct': False},
                                                {'text': 'boolean', 'is_correct': True},
                                                {'text': 'address', 'is_correct': False},
                                            ]
                                        },
                                    ]
                                }
                            },
                            {
                                'title': 'Functions and Modifiers',
                                'description': 'Writing functions and using modifiers in Solidity',
                                'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                                'content_type': 'video',
                                'duration_minutes': 30,
                            },
                        ]
                    },
                    {
                        'title': 'Smart Contract Security',
                        'description': 'Learn secure smart contract development',
                        'lessons': [
                            {
                                'title': 'Common Vulnerabilities',
                                'description': 'Reentrancy, overflow, and other attacks',
                                'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                                'content_type': 'video',
                                'duration_minutes': 35,
                                'has_quiz': True,
                                'quiz': {
                                    'title': 'Security Vulnerabilities Quiz',
                                    'passing_score': 80,
                                    'questions': [
                                        {
                                            'question_type': 'multiple_choice',
                                            'text': 'What is a reentrancy attack?',
                                            'points': 2,
                                            'answers': [
                                                {'text': 'When a contract calls another contract recursively', 'is_correct': True},
                                                {'text': 'When a contract runs out of gas', 'is_correct': False},
                                                {'text': 'When a contract is deployed twice', 'is_correct': False},
                                            ]
                                        },
                                        {
                                            'question_type': 'multiple_choice',
                                            'text': 'How can you prevent reentrancy attacks?',
                                            'points': 2,
                                            'answers': [
                                                {'text': 'Use the Checks-Effects-Interactions pattern', 'is_correct': True},
                                                {'text': 'Use more gas', 'is_correct': False},
                                                {'text': 'Make functions private', 'is_correct': False},
                                            ]
                                        },
                                    ]
                                }
                            },
                            {
                                'title': 'Secure Coding Patterns',
                                'description': 'Best practices for safe contracts',
                                'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                                'content_type': 'video',
                                'duration_minutes': 28,
                            },
                            {
                                'title': 'Access Control',
                                'description': 'Implementing proper access control mechanisms',
                                'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                                'content_type': 'video',
                                'duration_minutes': 25,
                                'has_quiz': True,
                                'quiz': {
                                    'title': 'Access Control Quiz',
                                    'passing_score': 70,
                                    'questions': [
                                        {
                                            'question_type': 'true_false',
                                            'text': 'All functions should be public by default.',
                                            'explanation': 'Functions should use the most restrictive visibility possible.',
                                            'points': 1,
                                            'answers': [
                                                {'text': 'True', 'is_correct': False},
                                                {'text': 'False', 'is_correct': True},
                                            ]
                                        },
                                    ]
                                }
                            },
                        ]
                    },
                    {
                        'title': 'DeFi Development',
                        'description': 'Building decentralized finance applications',
                        'lessons': [
                            {
                                'title': 'Introduction to DeFi',
                                'description': 'Understanding decentralized finance protocols',
                                'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                                'content_type': 'video',
                                'duration_minutes': 30,
                            },
                            {
                                'title': 'Building a Simple DEX',
                                'description': 'Creating a decentralized exchange',
                                'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                                'content_type': 'video',
                                'duration_minutes': 45,
                                'has_quiz': True,
                                'quiz': {
                                    'title': 'DeFi Development Quiz',
                                    'passing_score': 75,
                                    'questions': [
                                        {
                                            'question_type': 'multiple_choice',
                                            'text': 'What does DEX stand for?',
                                            'points': 1,
                                            'answers': [
                                                {'text': 'Decentralized Exchange', 'is_correct': True},
                                                {'text': 'Digital Exchange', 'is_correct': False},
                                                {'text': 'Direct Exchange', 'is_correct': False},
                                            ]
                                        },
                                    ]
                                }
                            },
                        ]
                    }
        ]
    },
    {
        'title': 'Web3 Development with JavaScript',
        'slug': 'web3-javascript',
        'description': 'Learn to build decentralized applications (dApps) using Web3.js and Ethers.js. Connect your frontend to blockchain networks and interact with smart contracts.',
        'category': 'Web Development',
        'difficulty_level': 'intermediate',
        'duration_hours': 30,
        'access_type': 'free',
        'token_cost': 0,
        'tags': ['web3', 'javascript', 'dapps', 'ethers.js'],
        'learning_objectives': [
            'Connect to blockchain networks',
            'Interact with smart contracts',
            'Build frontend dApps',
            'Handle wallet connections'
        ],
        'modules': [
            {
                'title': 'Web3.js Basics',
                'description': 'Introduction to Web3.js library',
                'lessons': [
                    {
                        'title': 'Setting up Web3',
                        'description': 'Installing and configuring Web3.js',
                        'content_url': 'https://www.youtube.com/embed/5uFvMU-u2_0',
                        'content_type': 'video',
                        'duration_minutes': 20,
                        'is_free_preview': True,
                        'transcript': 'Web3.js is a JavaScript library that allows you to interact with Ethereum nodes. It provides APIs for reading and writing data to the blockchain.',
                    },
                    {
                        'title': 'Connecting to Ethereum',
                        'description': 'Establishing connection to blockchain networks',
                        'content_url': 'https://www.youtube.com/embed/5uFvMU-u2_0',
                        'content_type': 'video',
                        'duration_minutes': 22,
                    },
                    {
                        'title': 'Reading from Blockchain',
                        'description': 'Querying contract state and reading data',
                        'content_url': 'https://www.youtube.com/embed/5uFvMU-u2_0',
                        'content_type': 'video',
                        'duration_minutes': 25,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Web3.js Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What does Web3.js allow you to do?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'Interact with blockchain from JavaScript', 'is_correct': True},
                                        {'text': 'Create smart contracts', 'is_correct': False},
                                        {'text': 'Mine cryptocurrency', 'is_correct': False},
                                    ]
                                },
                                {
                                    'question_type': 'true_false',
                                    'text': 'Web3.js can only read data, not write to the blockchain.',
                                    'explanation': 'Web3.js can both read from and write to the blockchain.',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'True', 'is_correct': False},
                                        {'text': 'False', 'is_correct': True},
                                    ]
                                },
                            ]
                        }
                    },
                ]
            },
            {
                'title': 'Interacting with Contracts',
                'description': 'Connecting and interacting with smart contracts',
                'lessons': [
                    {
                        'title': 'Loading Contract ABI',
                        'description': 'How to load and use contract ABIs',
                        'content_url': 'https://www.youtube.com/embed/5uFvMU-u2_0',
                        'content_type': 'video',
                        'duration_minutes': 28,
                    },
                    {
                        'title': 'Calling Contract Methods',
                        'description': 'Calling view and state-changing functions',
                        'content_url': 'https://www.youtube.com/embed/5uFvMU-u2_0',
                        'content_type': 'video',
                        'duration_minutes': 30,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Contract Interaction Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What is an ABI?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'Application Binary Interface - describes contract methods', 'is_correct': True},
                                        {'text': 'A wallet address', 'is_correct': False},
                                        {'text': 'A blockchain network', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                    {
                        'title': 'Sending Transactions',
                        'description': 'Sending transactions to smart contracts',
                        'content_url': 'https://www.youtube.com/embed/5uFvMU-u2_0',
                        'content_type': 'video',
                        'duration_minutes': 32,
                    },
                ]
            },
            {
                'title': 'Building dApps',
                'description': 'Creating complete decentralized applications',
                'lessons': [
                    {
                        'title': 'Wallet Integration',
                        'description': 'Connecting MetaMask and other wallets',
                        'content_url': 'https://www.youtube.com/embed/5uFvMU-u2_0',
                        'content_type': 'video',
                        'duration_minutes': 35,
                    },
                    {
                        'title': 'Event Handling',
                        'description': 'Listening to blockchain events',
                        'content_url': 'https://www.youtube.com/embed/5uFvMU-u2_0',
                        'content_type': 'video',
                        'duration_minutes': 28,
                    },
                ]
            }
        ]
    },
    {
        'title': 'AI-Powered Learning Systems',
        'slug': 'ai-learning-systems',
        'description': 'Explore how artificial intelligence is transforming education. Learn about recommendation systems, personalized learning paths, and adaptive content delivery.',
        'category': 'AI & Machine Learning',
        'difficulty_level': 'intermediate',
        'duration_hours': 25,
        'access_type': 'paid',
        'token_cost': 0,
        'price_usd': 99.00,
        'tags': ['ai', 'machine-learning', 'recommendation-systems', 'education'],
        'learning_objectives': [
            'Understand AI in education',
            'Build recommendation systems',
            'Create personalized learning paths',
            'Implement adaptive content'
        ],
        'modules': [
            {
                'title': 'Recommendation Algorithms',
                'description': 'Learn recommendation system algorithms',
                'lessons': [
                    {
                        'title': 'Introduction to Recommendation Systems',
                        'description': 'Overview of recommendation systems in education',
                        'content_url': 'https://www.youtube.com/embed/HnqkZVyC5_E',
                        'content_type': 'video',
                        'duration_minutes': 25,
                        'is_free_preview': True,
                    },
                    {
                        'title': 'Collaborative Filtering',
                        'description': 'User-based and item-based recommendations',
                        'content_url': 'https://www.youtube.com/embed/HnqkZVyC5_E',
                        'content_type': 'video',
                        'duration_minutes': 30,
                        'transcript': 'Collaborative filtering recommends items based on user behavior and preferences of similar users.',
                    },
                    {
                        'title': 'Content-Based Filtering',
                        'description': 'Feature-based recommendations',
                        'content_url': 'https://www.youtube.com/embed/HnqkZVyC5_E',
                        'content_type': 'video',
                        'duration_minutes': 28,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Recommendation Systems Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What is collaborative filtering?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'Finding similar users or items', 'is_correct': True},
                                        {'text': 'Analyzing content features', 'is_correct': False},
                                        {'text': 'Using neural networks', 'is_correct': False},
                                    ]
                                },
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What is the difference between collaborative and content-based filtering?',
                                    'points': 2,
                                    'answers': [
                                        {'text': 'Collaborative uses user behavior, content-based uses item features', 'is_correct': True},
                                        {'text': 'They are the same', 'is_correct': False},
                                        {'text': 'Content-based uses user behavior', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                ]
            },
            {
                'title': 'Personalized Learning Paths',
                'description': 'Creating adaptive learning experiences',
                'lessons': [
                    {
                        'title': 'Learning Path Design',
                        'description': 'Designing personalized learning journeys',
                        'content_url': 'https://www.youtube.com/embed/HnqkZVyC5_E',
                        'content_type': 'video',
                        'duration_minutes': 32,
                    },
                    {
                        'title': 'Adaptive Content Delivery',
                        'description': 'Adapting content based on learner progress',
                        'content_url': 'https://www.youtube.com/embed/HnqkZVyC5_E',
                        'content_type': 'video',
                        'duration_minutes': 28,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Adaptive Learning Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'true_false',
                                    'text': 'Adaptive learning adjusts content based on learner performance.',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'True', 'is_correct': True},
                                        {'text': 'False', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                ]
            }
        ]
    },
    {
        'title': 'Full-Stack Blockchain Development',
        'slug': 'fullstack-blockchain',
        'description': 'Build complete decentralized applications from frontend to smart contracts. Learn React, Node.js, and Solidity to create production-ready dApps.',
        'category': 'Full Stack',
        'difficulty_level': 'advanced',
        'duration_hours': 60,
        'access_type': 'token',
        'token_cost': 100,
        'tags': ['fullstack', 'react', 'solidity', 'dapps', 'blockchain'],
        'learning_objectives': [
            'Build full-stack dApps',
            'Integrate frontend with blockchain',
            'Handle wallet connections',
            'Deploy production applications'
        ],
        'modules': [
            {
                'title': 'Project Setup',
                'description': 'Setting up a full-stack blockchain project',
                'lessons': [
                    {
                        'title': 'React + Web3 Setup',
                        'description': 'Creating a dApp project structure',
                        'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                        'content_type': 'video',
                        'duration_minutes': 25,
                        'is_free_preview': True,
                        'transcript': 'Setting up a React application with Web3 integration is the foundation of any dApp. We will use create-react-app and install necessary dependencies.',
                    },
                    {
                        'title': 'Smart Contract Integration',
                        'description': 'Connecting frontend to smart contracts',
                        'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                        'content_type': 'video',
                        'duration_minutes': 30,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Project Setup Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What libraries are typically needed for Web3 integration?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'Web3.js or Ethers.js', 'is_correct': True},
                                        {'text': 'jQuery', 'is_correct': False},
                                        {'text': 'Angular', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                    {
                        'title': 'State Management',
                        'description': 'Managing application state with Redux or Context',
                        'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                        'content_type': 'video',
                        'duration_minutes': 35,
                    },
                ]
            },
            {
                'title': 'Building the Frontend',
                'description': 'Creating user interfaces for dApps',
                'lessons': [
                    {
                        'title': 'Wallet Connection UI',
                        'description': 'Building wallet connection components',
                        'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                        'content_type': 'video',
                        'duration_minutes': 28,
                    },
                    {
                        'title': 'Transaction Handling',
                        'description': 'Implementing transaction UI and feedback',
                        'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                        'content_type': 'video',
                        'duration_minutes': 32,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Frontend Development Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'true_false',
                                    'text': 'Wallet connection is necessary for reading blockchain data.',
                                    'explanation': 'Reading is public, but wallet connection is needed for writing transactions.',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'True', 'is_correct': False},
                                        {'text': 'False', 'is_correct': True},
                                    ]
                                },
                            ]
                        }
                    },
                ]
            },
            {
                'title': 'Smart Contract Development',
                'description': 'Writing and testing smart contracts',
                'lessons': [
                    {
                        'title': 'Contract Architecture',
                        'description': 'Designing contract structure for dApps',
                        'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                        'content_type': 'video',
                        'duration_minutes': 35,
                    },
                    {
                        'title': 'Testing Contracts',
                        'description': 'Writing tests with Truffle or Hardhat',
                        'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                        'content_type': 'video',
                        'duration_minutes': 40,
                    },
                ]
            },
            {
                'title': 'Deployment',
                'description': 'Deploying your dApp to production',
                'lessons': [
                    {
                        'title': 'Contract Deployment',
                        'description': 'Deploying smart contracts to testnet and mainnet',
                        'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                        'content_type': 'video',
                        'duration_minutes': 35,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Deployment Quiz',
                            'passing_score': 75,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'Which network should you deploy to first?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'Testnet (like Sepolia)', 'is_correct': True},
                                        {'text': 'Mainnet', 'is_correct': False},
                                        {'text': 'Local blockchain', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                    {
                        'title': 'Frontend Deployment',
                        'description': 'Deploying React apps to hosting platforms',
                        'content_url': 'https://www.youtube.com/embed/p3o7Qd1g3es',
                        'content_type': 'video',
                        'duration_minutes': 25,
                    },
                ]
            }
        ]
    },
    {
        'title': 'Introduction to Cryptocurrency Trading',
        'slug': 'crypto-trading-basics',
        'description': 'Learn the fundamentals of cryptocurrency trading, technical analysis, and market strategies. Understand risk management and portfolio diversification.',
        'category': 'Finance',
        'difficulty_level': 'beginner',
        'duration_hours': 15,
        'access_type': 'paid',
        'token_cost': 0,
        'price_usd': 49.00,
        'tags': ['trading', 'cryptocurrency', 'finance', 'investment'],
        'learning_objectives': [
            'Understand crypto markets',
            'Learn technical analysis',
            'Develop trading strategies',
            'Manage risk effectively'
        ],
        'modules': [
            {
                'title': 'Market Basics',
                'description': 'Understanding cryptocurrency markets',
                'lessons': [
                    {
                        'title': 'Understanding Exchanges',
                        'description': 'How cryptocurrency exchanges work',
                        'content_url': 'https://www.youtube.com/embed/cjxXxyo2pPg',
                        'content_type': 'video',
                        'duration_minutes': 20,
                        'is_free_preview': True,
                        'transcript': 'Cryptocurrency exchanges are platforms where users can buy, sell, and trade digital assets. They can be centralized or decentralized.',
                    },
                    {
                        'title': 'Order Types',
                        'description': 'Market, limit, and stop orders',
                        'content_url': 'https://www.youtube.com/embed/cjxXxyo2pPg',
                        'content_type': 'video',
                        'duration_minutes': 22,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Order Types Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What is a limit order?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'An order to buy/sell at a specific price or better', 'is_correct': True},
                                        {'text': 'An order that executes immediately', 'is_correct': False},
                                        {'text': 'An order that cancels automatically', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                    {
                        'title': 'Trading Basics',
                        'description': 'Introduction to trading strategies',
                        'content_url': 'https://www.youtube.com/embed/cjxXxyo2pPg',
                        'content_type': 'video',
                        'duration_minutes': 25,
                    },
                ]
            },
            {
                'title': 'Technical Analysis',
                'description': 'Analyzing price charts and patterns',
                'lessons': [
                    {
                        'title': 'Candlestick Patterns',
                        'description': 'Understanding candlestick charts',
                        'content_url': 'https://www.youtube.com/embed/cjxXxyo2pPg',
                        'content_type': 'video',
                        'duration_minutes': 28,
                    },
                    {
                        'title': 'Support and Resistance',
                        'description': 'Identifying key price levels',
                        'content_url': 'https://www.youtube.com/embed/cjxXxyo2pPg',
                        'content_type': 'video',
                        'duration_minutes': 25,
                        'has_quiz': True,
                        'quiz': {
                            'title': 'Technical Analysis Quiz',
                            'passing_score': 70,
                            'questions': [
                                {
                                    'question_type': 'multiple_choice',
                                    'text': 'What is a support level?',
                                    'points': 1,
                                    'answers': [
                                        {'text': 'A price level where buying pressure is strong', 'is_correct': True},
                                        {'text': 'A price level where selling pressure is strong', 'is_correct': False},
                                        {'text': 'The highest price ever reached', 'is_correct': False},
                                    ]
                                },
                            ]
                        }
                    },
                ]
            },
            {
                'title': 'Risk Management',
                'description': 'Managing risk in cryptocurrency trading',
                'lessons': [
                    {
                        'title': 'Position Sizing',
                        'description': 'Determining how much to invest',
                        'content_url': 'https://www.youtube.com/embed/cjxXxyo2pPg',
                        'content_type': 'video',
                        'duration_minutes': 22,
                    },
                    {
                        'title': 'Stop Loss and Take Profit',
                        'description': 'Setting exit strategies',
                        'content_url': 'https://www.youtube.com/embed/cjxXxyo2pPg',
                        'content_type': 'video',
                        'duration_minutes': 20,
                    },
                ]
            }
        ]
    }
]


class Command(BaseCommand):
    help = 'Seed the database with sample courses'

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed courses...')
        
        # Delete existing courses and related data
        self.stdout.write('Cleaning existing course data...')
        deleted_courses = Course.objects.count()
        Answer.objects.all().delete()
        Question.objects.all().delete()
        Quiz.objects.all().delete()
        Lesson.objects.all().delete()
        Module.objects.all().delete()
        Course.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_courses} existing courses and all related data'))
        
        # Get or create admin user as instructor
        admin_user, created = User.objects.get_or_create(
            email='admin@lms.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.email}'))
        else:
            self.stdout.write(f'Using existing admin user: {admin_user.email}')
        
        # Create categories
        categories = {}
        for course_data in SAMPLE_COURSES:
            category_name = course_data['category']
            if category_name not in categories:
                category, created = CourseCategory.objects.get_or_create(
                    name=category_name,
                    defaults={
                        'slug': category_name.lower().replace(' ', '-'),
                        'description': f'{category_name} related courses'
                    }
                )
                categories[category_name] = category
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created category: {category_name}'))
        
        # Create courses
        courses_created = 0
        for course_data in SAMPLE_COURSES:
            # Copy course_data to avoid modifying the original
            course_data_copy = course_data.copy()
            category = categories[course_data_copy.pop('category')]
            modules_data = course_data_copy.pop('modules', [])
            
            # Create course (we already deleted all, so this will always create new)
            course = Course.objects.create(
                category=category,
                instructor=admin_user,
                created_by=admin_user,
                status='published',
                published_at=timezone.now(),
                **course_data_copy
            )
            
            courses_created += 1
            self.stdout.write(self.style.SUCCESS(f'Created course: {course.title}'))
                
            # Create modules and lessons
            for module_order, module_data in enumerate(modules_data, 1):
                lessons_data = module_data.pop('lessons', [])
                module_description = module_data.pop('description', '')
                
                module = Module.objects.create(
                    course=course,
                    order=module_order,
                    title=module_data['title'],
                    description=module_description
                )
                
                for lesson_order, lesson_data in enumerate(lessons_data, 1):
                    # Handle quiz data
                    quiz_data = lesson_data.pop('quiz', None)
                    has_quiz = lesson_data.pop('has_quiz', False)
                    
                    # Create lesson
                    lesson = Lesson.objects.create(
                        module=module,
                        order=lesson_order,
                        **lesson_data
                    )
                    
                    # Create quiz if needed
                    if has_quiz and quiz_data:
                        quiz = Quiz.objects.create(
                            lesson=lesson,
                            title=quiz_data.get('title', f'Quiz: {lesson.title}'),
                            description=quiz_data.get('description', ''),
                            passing_score=quiz_data.get('passing_score', 70),
                            max_attempts=quiz_data.get('max_attempts', 3),
                            shuffle_questions=quiz_data.get('shuffle_questions', True),
                        )
                        
                        # Create questions and answers
                        questions_data = quiz_data.get('questions', [])
                        for question_order, question_data in enumerate(questions_data, 1):
                            answers_data = question_data.pop('answers', [])
                            
                            question = Question.objects.create(
                                quiz=quiz,
                                question_type=question_data.get('question_type', 'multiple_choice'),
                                text=question_data.get('text', ''),
                                explanation=question_data.get('explanation', ''),
                                order=question_order,
                                points=question_data.get('points', 1),
                            )
                            
                            # Create answers
                            for answer_order, answer_data in enumerate(answers_data, 1):
                                Answer.objects.create(
                                    question=question,
                                    text=answer_data.get('text', ''),
                                    is_correct=answer_data.get('is_correct', False),
                                    order=answer_order
                                )
                        
                        self.stdout.write(f'    Created quiz with {len(questions_data)} questions for: {lesson.title}')
                
                self.stdout.write(f'  Created module: {module.title} with {len(lessons_data)} lessons')
        
        # Update CourseVector for AI recommendations (if it exists)
        try:
            from src.services.ai_recommendations.models import CourseVector
            
            for course in Course.objects.all():
                CourseVector.objects.update_or_create(
                    course_id=course.id,
                    defaults={
                        'course_name': course.title,
                        'category': course.category.name if course.category else 'Uncategorized',
                        'difficulty_level': course.difficulty_level,
                        'tags': course.tags,
                        'total_enrollments': course.total_enrollments,
                        'avg_rating': float(course.average_rating),
                        'completion_rate': 0.0,
                        'feature_vector': {
                            'difficulty': {'beginner': 0, 'intermediate': 0, 'advanced': 0}.get(course.difficulty_level, 0),
                            'category': course.category.name if course.category else '',
                            'duration': course.duration_hours,
                        }
                    }
                )
            self.stdout.write(self.style.SUCCESS('Updated CourseVector for recommendations'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not update CourseVector: {e}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully seeded {courses_created} courses!'
        ))

