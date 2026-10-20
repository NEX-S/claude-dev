import datetime,hashlib,json,os,pathlib,signal,subprocess,time
run=pathlib.Path(__file__).resolve().parent
argv=json.loads((run/'argv.json').read_text()); start=time.monotonic()
with (run/'native.jsonl').open('w') as out,(run/'native.stderr').open('w') as err:
 process=subprocess.Popen(argv,cwd=run/'project',stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
 state={'pid':process.pid,'session_id':json.loads((run/'manifest.json').read_text())['session_id'],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixed_timeout_seconds':180}
 (run/'live.json').write_text(json.dumps(state,indent=2)+'\n'); print(json.dumps(state),flush=True)
 try:
  code=process.wait(timeout=180); timed_out=False
 except subprocess.TimeoutExpired:
  timed_out=True; os.killpg(process.pid,signal.SIGKILL); code=process.wait(timeout=10)
 state.update(exit_code=code,timed_out=timed_out,elapsed_seconds=time.monotonic()-start,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 (run/'terminal.json').write_text(json.dumps(state,indent=2)+'\n'); print(json.dumps(state),flush=True)
for verifier in ('acceptance','supplement'):
 result=subprocess.run(['python3',str(run/f'{verifier}.py'),str(run/'project')],capture_output=True,text=True,timeout=30)
 (run/f'final-{verifier}.json').write_text(result.stdout); (run/f'final-{verifier}.stderr').write_text(result.stderr)
 print(json.dumps({'verifier':verifier,'exit_code':result.returncode,'passed':json.loads(result.stdout).get('passed') if result.returncode==0 else None}),flush=True)
fixture=run/'project/existing.db'
print(json.dumps({'existing_db_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest()}),flush=True)
