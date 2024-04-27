import shutil

for i in range(3600):
    fp = f'~/data_asr/pickled/{i}.pkl'
    dst = f'~/pickled/{i}.pkl'
    shutil.copyfile(fp, dst)
