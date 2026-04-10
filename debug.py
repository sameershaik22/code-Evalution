from src.modules.ingestion import Ingestor
i = Ingestor()
subs = i.load_submissions('assignments/hw1/config.json', 'submissions/hw1')
print("Number of submissions:", len(subs))
for idx, s in enumerate(subs):
    print(f"\nSubmission {idx}:")
    print("student_id:", s.get('student_id'))
    print("config type:", type(s.get('config')))
    print("config:", s.get('config'))
    print("code type:", type(s.get('code')))
    print("code len:", len(s.get('code', '')))