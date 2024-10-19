from invoke import task

source_path= 'source/gw-backup-sample'
destination_path='destination'

@task
def clean(context, destination=destination_path):
    context.run(f"rm -fr {destination} &> /dev/null")

@task(default=True,pre=[clean])
def run(context, source=source_path, destination=destination_path):
    context.run(f"python extract.py --source {source} --destination {destination}")

@task(pre=[clean])
def test(context):
    context.run(f"python test.py")