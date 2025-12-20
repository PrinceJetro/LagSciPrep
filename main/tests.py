from openai import OpenAI
import openai
openai.api_key = "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"
client = OpenAI(api_key="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")



prompt = f"""
You are an expert exam question generator.

Generate 50 multiple-choice questions from the content below.
Each question must follow this exact JSON format:

        {{
            "question": "",
            "options": {{
                "A": "",
                "B": "",
                "C": "",
                "D": ""
            }},
            "correct_option": "",
            "explanation": "",
            "hint": ""
        }},

DO NOT add commentary. Return a JSON array.

CONTENT:

Course Learning Outcomes
By the end of the course, students are expected to:
•	Explain the basic components of computers and other computing devices.
•	Describe various applications of computers.
•	Explain information processing and its societal role.
•	Describe internet applications and impacts.
•	Explain areas of computing disciplines and specializations.
•	Demonstrate practical skills in using computers and the internet.
________________________________________
Course Content and Outline
Week	Topic
1	Introduction to Computing Science
2	Evolution of Computers
3	Computer System: Components of a Computer System
4	Introduction to Software and Programming Languages
5-7	Continued lectures and First Continuous Assessment (CA1)
8-10	Further Lectures
11	Second Continuous Assessment (CA2)
12	Final Examination
Core Concepts Covered in the Lecture
1. Definition of a Computer
•	A computer is an electronic device that stores, processes, and communicates information.
•	It is described as a super smart machine that follows instructions (programs) to perform specific tasks.
•	The principle “garbage in, garbage out” was emphasized, meaning the computer output depends on the quality of input.
2. Five Core Functionalities of a Computer
Functionality	Description
Input	Devices like keyboard, mouse, touch screen used to enter data/instructions into the computer.
Processing	Conducted by the CPU; it processes instructions and data to produce results.
Storage	Temporary (RAM) or permanent (hard drive, SSD) storage of data and programs.
Output	Results displayed on screen or printed via printers (soft and hard copies).
Communication	Connection to other devices through network, internet, or direct links (wired/wireless).
•	Students actively participated by describing processing, storage, input, output, and communication functionalities.
________________________________________
3. Computer Components
•	Hardware: Physical parts of the computer system that can be touched.
o	Examples: Monitor, keyboard, mouse, hard drive, system unit, sound card.
•	Software: Programs and operating systems that run on hardware.
•	Input Devices: Devices that translate human-understandable data into computer-readable data.
o	Examples include keyboard, mouse, touchscreen, graphic tablet, remote control.
•	Central Processing Unit (CPU):
o	Known as the brain of the computer.
o	Responsible for processing and controlling all functions.
o	Comprised of three main parts:
	Arithmetic Logic Unit (ALU): Executes arithmetic (addition, subtraction, multiplication) and logical operations (comparisons).
	Control Unit (CU): Controls and coordinates computer components, reads instructions, increments program counter.
	Registers: Hold data and instructions temporarily during execution.
________________________________________
4. Memory Types
Memory Type	Description	Characteristics	Examples
Primary Memory	Temporary storage of data and instructions during processing. Volatile in nature (data lost when power off).	Volatile (temporary)	RAM (Random Access Memory)
Secondary Memory	Permanent storage of data and programs, retained even when power is off.	Non-volatile (permanent)	Hard drives, SSD, optical drives, flash drives
•	RAM is volatile, meaning data is lost when power is off.
•	ROM (Read Only Memory) stores permanent data that cannot be modified by users.
•	Secondary memory keeps data permanently and includes devices like hard drives and flash drives.
•	Students discussed the importance of saving work regularly due to RAM’s volatility.
________________________________________
5. Input and Output Devices
•	Input devices translate human input into machine-readable data.
•	Output devices convert processed data into human-readable form.
•	Examples of output devices include monitors (CRT, LCD), printers (laser, inkjet), and speakers.
•	There was a detailed discussion about whether a typewriter is input or output:
o	The consensus was that a typewriter is an output device, as it mechanically prints text.
o	The keyboard part of a typewriter can be considered an input device but it is generally not part of a computer system.
________________________________________
6. Software
•	System Software:
o	Includes operating systems and utility programs like defragmenters, file managers, display managers.
o	Responsible for managing hardware components and providing a platform for application software.
•	Application Software:
o	Software designed to accomplish specific tasks for users.
o	Examples: Microsoft Word (word processing), Excel (spreadsheets/calculations), PowerPoint (presentations).
Comparison: System Software vs Application Software
System Software: Controls hardware and provides basic functionality.
Includes OS, utilities, device drivers.
7. Units of Measurement for Computer Storage
Unit	Size (Approximate)
Bit	Binary digit (0 or 1)
Byte	8 bits
Kilobyte (KB)	1,024 bytes
Megabyte (MB)	1,024 KB
Gigabyte (GB)	1,024 MB
•	Students were encouraged to familiarize themselves with storage units and their sizes.
•	Flash drives with sizes like 32GB were cited as common examples.
________________________________________
8. Characteristics of Computers
•	Speed: Processes data quickly.
•	Accuracy: Delivers precise output.
•	Diligency: Can perform repetitive tasks without fatigue.
•	Storage: Ability to hold vast amounts of data.
•	Capability: Can perform multiple types of tasks.
•	Versatility: Can be used in various fields and applications.
________________________________________
9. Applications of Computers
•	Business
•	Education
•	Healthcare
•	Science and Research
•	Entertainment
•	Communication
•	Transportation
•	Finance
________________________________________
Key Insights
•	The CPU is the heart and brain of the computer system, executing instructions and managing operations.
•	Differentiating between hardware (physical devices) and software (programs) is fundamental.
•	Memory types (RAM vs ROM vs secondary memory) have distinct characteristics crucial for system performance and data management.
•	The five core functionalities of a computer provide a framework for understanding how computers operate.
•	System software vs application software: Understanding their roles clarifies how software interacts with hardware and user needs.
•	Computer storage units are fundamental for grasping data size and capacity.
•	Regular attendance, use of course materials, and participation are emphasized for academic success.
________________________________________
Timeline Table: Course Content Delivery
Week	Topic/Activity	Notes
1	Introduction and Course Orientation	Course codes, registration, learning outcomes explained
2	Evolution of Computers	Historical context of computing
3	Computer System Components	Hardware/software overview, CPU details
4	Software Overview & Programming Languages	Distinction between system and application software
5-7	Lectures and Continuous Assessment 1	Use of workbook for CA1
8-10	Further Lectures	Deepening understanding
11	Continuous Assessment 2	Second workbook use
12	Final Examination	70% of total grade
Summary Table: CPU Components and Functions
CPU Component	Function Description
Arithmetic Logic Unit	Performs arithmetic calculations and logical comparisons
Control Unit	Directs and coordinates all computer operations by reading and executing instructions
Registers	Small storage locations holding data and instructions temporarily
FAQ Extracted from the Lecture
•	Q: Should 100 level students register with FSC 1113 or 101?
A: Register with course code 101. FSC 1113 is for carryover students.
•	Q: Is the CPU hardware or software?
A: The CPU is hardware; it is a physical unit you can see and touch.
•	Q: What does volatile mean in memory context?
A: Volatile memory loses its data when power is off (e.g., RAM).
•	Q: Is a typewriter an input or output device?
A: A typewriter is an output device, as it prints text mechanically.
•	Q: Can hardware be repaired or upgraded?
A: Yes, most hardware devices like mouse, printer, and others can be repaired or upgraded.
________________________________________
Conclusion
This introductory lecture thoroughly covers the foundational concepts of computing, emphasizing the importance of understanding computer components, software categories, memory types, and the practicalities of course registration and participation. The instructor encourages active student engagement, proper use of learning materials, and regular attendance to ensure successful mastery of computing fundamentals.
Key takeaway: A computer is a super smart machine that processes input, stores, outputs, and communicates information, driven by its CPU and supported by hardware and software working in tandem.
 

Expanded Notes on Core Concepts of a Computer
1. Definition of a Computer
A computer is an electronic device capable of receiving data (input), processing it according to a set of instructions (programs), storing it for current or future use, and producing results (output).
Key Ideas
•	A computer is a smart machine, but not intelligent on its own — it only does what it is instructed to do.
•	The principle “Garbage In, Garbage Out (GIGO)” means:
o	If wrong or poor-quality data is entered → incorrect or poor-quality output will be produced.
o	Good input leads to good output.
Simple Explanation
A computer acts like a very fast assistant: it follows your commands exactly and never guesses.
________________________________________
2. Five Core Functionalities of a Computer
These functions describe everything a computer can do:
| Functionality | Description |
|----------------------|------------------|
| Input | Accepts data and instructions through devices like keyboard, mouse, touchscreen, scanner, or microphone. |
| Processing | The CPU (Central Processing Unit) processes data using instructions from the software. This is where calculations and decision-making happen. |
| Storage | Saves data temporarily (RAM) or permanently (Hard Drive, SSD, Flash drive). |
| Output | Produces results that users can see, hear, or use — e.g., monitor display, speakers, printer. |
| Communication | Sends and receives data with other devices through networks, Bluetooth, Wi-Fi, or the internet. |
Class Activity Highlight
Students successfully identified and described examples of:
•	Input (typing on a keyboard)
•	Processing (CPU calculating)
•	Storage (saving a file)
•	Output (displaying results on screen)
•	Communication (sending an email)
________________________________________
3. Components of a Computer
A. Hardware
Physical components of the computer that you can touch and see.
Examples:
•	Monitor
•	Keyboard & Mouse
•	Hard drive / SSD
•	System Unit
•	Speakers
•	Graphic card / Sound card
•	Cables, motherboard, power supply
B. Software
Programs and operating systems that tell the hardware what to do.
Types of Software
•	System Software: Operating systems like Windows, macOS, Linux.
•	Application Software: Word processors, games, browsers, media players.
________________________________________
4. Input Devices
Devices that convert human-readable information into a form the computer can understand.
Examples
•	Keyboard
•	Mouse
•	Touchscreen
•	Graphic tablet
•	Remote control
•	Barcode scanner
•	Microphone
•	Joystick
•	Light pen
________________________________________
5. Central Processing Unit (CPU)
The CPU is called the brain of the computer because it performs all major processing and controls every operation.
Major Components of the CPU
1. Arithmetic Logic Unit (ALU)
•	Performs arithmetic operations:
addition, subtraction, multiplication, division.
•	Performs logical operations:
comparisons like greater than (>), less than (<), equal (=).
2. Control Unit (CU)
•	Directs the operations of the computer.
•	Tells other components when and how to work.
•	Reads instructions from memory.
•	Increments the program counter (moves to the next instruction).
3. Registers
•	Very small, very fast temporary memory inside the CPU.
•	Store data and instructions the CPU is currently working with.
Summary
The CPU:
•	Fetches instructions
•	Decodes them
•	Executes operations
This cycle repeats millions to billions of times per second.
________________________________________
6. How All Parts Work Together
1.	Input: User presses a key.
2.	Processing: CPU interprets the keystroke.
3.	Storage: Data is saved into RAM or disk.
4.	Output: Character appears on the screen.
5.	Communication: File may be shared online.


4. Memory Types
Memory refers to the parts of the computer where data is stored temporarily or permanently. There are two major categories: primary memory and secondary memory.
Memory Types Overview
Memory Type	Description	Characteristics	Examples
Primary Memory	Stores data and instructions currently being processed by the CPU.	• Volatile (data is lost when the computer is turned off) 
• Fast access time	RAM (Random Access Memory), ROM
Secondary Memory	Long-term/permanent storage of files, software, and data.	• Non-volatile (keeps data even when power is off) 
• Slower than RAM	Hard Disk Drive, SSD, Flash Drive, CD/DVD
________________________________________
Primary Memory Explained
1. RAM (Random Access Memory)
•	Temporary storage used during processing.
•	Volatile: data disappears once power goes off.
•	Determines how fast and smoothly programs run.
•	More RAM = better performance.
2. ROM (Read Only Memory)
•	Non-volatile, but still classified as primary memory because it is directly accessible by the CPU.
•	Stores permanent instructions needed to boot/start the computer.
•	Cannot be modified by the user.
Class Discussion Insight
Students emphasized the importance of saving work regularly, because:
•	Any unsaved work stored temporarily in RAM will be lost if the system shuts down suddenly.
________________________________________
5. Input and Output Devices
Input Devices
Input devices convert human actions or data into a form the computer understands.
Examples include:
•	Keyboard
•	Mouse
•	Touchscreen
•	Microphone
•	Scanner
•	Digital camera
•	Joystick
•	Barcode reader
Output Devices
Output devices transform processed data into forms humans can read, see, or hear.
Examples include:
•	Monitors: CRT, LCD, LED
•	Printers: Inkjet, Laser
•	Speakers & Headphones
•	Projectors
________________________________________
Is a Typewriter Input or Output? — Class Debate
There was an engaging discussion about the classification of a typewriter.
Conclusion:
•	A traditional typewriter is an output device because it directly prints characters onto paper.
•	The keys function like an input mechanism, but:
o	It does not send data to a computer.
o	It works mechanically, not electronically.
Thus, a typewriter is not considered a computer device but can be described as mechanical output equipment.
________________________________________
6. Software
Software refers to the set of instructions that tell the computer what to do. It is divided into two major types:
________________________________________
A. System Software
System software manages hardware components and provides the environment in which other software runs.
Examples
•	Operating Systems: Windows, macOS, Linux, Android
•	Utility Programs:
o	Disk Defragmenter
o	File Manager
o	Display Manager
o	Antivirus software
•	Device Drivers: Help hardware communicate with the operating system.
Functions
•	Manage memory and CPU
•	Control input and output
•	Handle file management
•	Provide user interface
________________________________________
B. Application Software
These are programs designed to help users perform specific tasks.
Examples
•	Microsoft Word → Word processing
•	Excel → Calculations and spreadsheets
•	PowerPoint → Presentations
•	Browsers → Internet access
•	Media Players → Audio/video playback
•	Games → Entertainment
________________________________________
Comparison: System Software vs Application Software
System Software	Application Software
Controls hardware and manages system operations.	Helps users perform specific personal or professional tasks.
Runs in the background.	Runs on top of system software.
Provides basic functions for the computer to work.	Provides tools for users to create documents, play games, etc.
Examples: Operating systems, device drivers, utilities.	Examples: Word processors, browsers, games, spreadsheets.
________________________________________
If you'd like, I can help you:


7. Units of Measurement for Computer Storage
Computer data is measured using binary units. Each level represents roughly 1,024 units of the previous level because computers operate in base-2 (binary).
Storage Units Table
Unit	Meaning / Size
Bit	Smallest unit of data; a binary digit (0 or 1).
Byte	8 bits; usually represents one character (e.g., a letter or symbol).
Kilobyte (KB)	1,024 bytes
Megabyte (MB)	1,024 KB
Gigabyte (GB)	1,024 MB
Terabyte (TB) (for completeness)	1,024 GB
Petabyte (PB) (very large systems)	1,024 TB
Class Emphasis
•	Students were encouraged to memorize the sequence and sizes.
•	Real-life example:
A 32GB flash drive can store thousands of documents, images, or songs.
________________________________________
8. Characteristics of Computers
Computers possess several key characteristics that make them indispensable in modern life:
1. Speed
Computers can process millions to billions of instructions per second.
2. Accuracy
They deliver correct results as long as correct instructions and data are provided.
3. Diligence
Computers do not get tired, bored, or lose concentration, even during repetitive tasks.
4. Storage Capacity
They can store enormous amounts of data, from small text files to entire databases and multimedia.
5. Capability
Computers can perform a wide variety of tasks, such as calculations, graphics rendering, simulations, communication, etc.
6. Versatility
They are used across multiple fields — business, medicine, engineering, entertainment, education, and more.
________________________________________
9. Applications of Computers
Computers have become important tools in nearly every sector:
A. Business
•	Payroll processing
•	Data management
•	Online transactions
•	Inventory control
B. Education
•	E-learning platforms
•	Research
•	Computer-based testing
•	Multimedia teaching tools
C. Healthcare
•	Hospital management systems
•	Patient record storage
•	Diagnostic equipment
•	Telemedicine
D. Science and Research
•	Simulations
•	Data analysis
•	Space exploration
•	Laboratory technology
E. Entertainment
•	Video games
•	Music & movie production
•	Streaming services
F. Communication
•	Email
•	Video conferencing
•	Social media
•	Instant messaging
G. Transportation
•	GPS navigation systems
•	Automated ticketing
•	Traffic control
H. Finance
•	Online banking
•	ATM operations
•	Stock market analysis
________________________________________
Key Insights from the Lesson
•	The CPU acts as the brain and heart of the computer — it executes instructions, manages processes, and controls other components.
•	Distinguishing between hardware (physical components) and software (programs and instructions) is essential for understanding how computers function.
•	Memory types are different:
o	RAM: temporary, volatile, affects speed.
o	ROM: permanent instructions.
o	Secondary storage: long-term data storage.
•	The five core computer functionalities — input, processing, storage, output, communication — provide a complete model of how computers work.
•	Understanding the difference between system software (OS, utilities, drivers) and application software (Word, games, browsers) helps clarify how software interacts with hardware.
•	Storage units like KB, MB, and GB are vital for understanding file sizes and memory capacity in computing.


"""
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
)

questions = response.choices[0].message.content
print(questions)
