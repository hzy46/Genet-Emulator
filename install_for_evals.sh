cd ..

sudo add-apt-repository universe
sudo apt-get update
sudo apt-get -y install mahimahi xvfb python3-pip python3-tk unzip virtualenv
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get -yf install ./google-chrome-stable_current_amd64.deb
pip3 install virtualenv

virtualenv -p python3 tf_venv
echo "$(pwd)/Genet/src/emulator/abr" > tf_venv/lib/python3.6/site-packages/abr_emu.pth
source tf_venv/bin/activate

pip3 install numpy tensorflow==2.6.2 selenium pyvirtualdisplay numba torch tflearn xvfbwrapper matplotlib scipy

cd Genet/src/emulator/abr/pensieve/virtual_browser/abr_browser_dir

chrome_version=$(google-chrome --version | awk '{print $3}')
wget https://storage.googleapis.com/chrome-for-testing-public/${chrome_version}/linux64/chromedriver-linux64.zip
# wget https://chromedriver.storage.googleapis.com/${chrome_version}/chromedriver_linux64.zip
unzip chromedriver-linux64.zip # (overwrite the old one if needed)
cp ./chromedriver-linux64/chromedriver ./chromedriver