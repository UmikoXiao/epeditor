import os
idd_dir=os.path.join(os.path.dirname(__file__),r'idd')
idd_files={idd.split('E')[0][1:-1]:os.path.join(idd_dir,idd) for idd in os.listdir(idd_dir)}