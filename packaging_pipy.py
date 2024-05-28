import os, shutil

def packaging_pipy():
    # Copy files
    shutil.rmtree('dist')

    shutil.copytree('oauth_emailbackend/oauth_emailbackend', 
                    'dist/src/oauth_emailbackend')
    for f in ('LICENSE', 'README.md', 'pyproject.toml'):
        if os.path.exists(f):
            shutil.copyfile(f, os.path.join('dist', f))

    # Build pypi package
    os.chdir('dist')
    os.system('python3 -m build')

    # 업로드하려면...
    # twine upload dist/dist/*

if __name__ == "__main__":
    packaging_pipy()