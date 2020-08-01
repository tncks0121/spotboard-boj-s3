import ujson
import sys
import requests
import boto3
import datetime

boto3_session = boto3.session.Session(profile_name='spotboard-s3-user')
s3_client = boto3_session.client('s3')

BUCKET_NAME = 'scoreboard-2020.ucpc.me'

CONTEST_ID = 524
OPTION = sys.argv[1]
assert OPTION in ['public', 'contest']

THRES_PROBLEM = 9
THRES_TIME = 180
BANNED_TEAMS = ['50000']

# Chrome에서 https://www.acmicpc.net/contest/spotboard/all/524/runs.json 를 호출할 때
# 보내는 헤더를 긁어서 붙임.
# 보안을 위해 일단 공유할 때는 생략합니다.
with open("headers.txt") as headers_file:
    headers = [row.split(': ', 2) for row in headers_file.read().strip().split('\n')]

def upload_file(to, content):
    with open(f"{to}", "w") as f:
        f.write(content)
    s3_client.upload_file(f"{to}", BUCKET_NAME, to, ExtraArgs={
        'Metadata': {
            'Cache-Control': 'max-age=1'
        }
    })

if OPTION == 'contest':
    req = requests.get(f"https://www.acmicpc.net/contest/spotboard/all/{CONTEST_ID}/contest.json",
        headers={key: value for key, value in headers})
    data = req.json()
    data['teams'] = [team for team in data['teams'] if team['id'] not in BANNED_TEAMS]
    upload_file('api/contest.json', ujson.dumps(data))
    exit(0)

req = requests.get(f"https://www.acmicpc.net/contest/spotboard/all/{CONTEST_ID}/runs.json",
    headers={key: value for key, value in headers})

data = req.json()

ac_problems_of_teams = {}
frozen_teams = set()

# IOI 2020 무시
data['runs'] = [run for run in data['runs'] if run['team'] not in BANNED_TEAMS]

for run in data['runs']:
    if run['team'] not in ac_problems_of_teams:
        ac_problems_of_teams[run['team']] = set()
    ps = ac_problems_of_teams[run['team']]
    if run['result'] == 'Yes':
        ps.add(run['problem'])

    run['frozen'] = False
    if run['team'] in frozen_teams or run['submissionTime'] >= THRES_TIME:
        if OPTION == 'public':
            run['result'] = ''
        run['frozen'] = True

    if len(ps) >= THRES_PROBLEM:
        frozen_teams.add(run['team'])

if OPTION == 'award':
    data['runs'].sort(key=lambda x: (x['frozen'], x['id']))
    with open("runs.json", "w") as f:
        f.write(ujson.dumps(data))
else:
    upload_file('api/runs.json', ujson.dumps(data))
    upload_file('api/changed_runs.json', ujson.dumps(data))

print('Succeeded!')
print(datetime.datetime.now())