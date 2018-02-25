import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# if sys.version_info < (2, 6): json?

setup(

      name = "Belle, The Webpage Assistant",
      version = "0.1",

      description = """These days, virtual assistants such as Siri, Cortana, Google assistants, Amazon Alexa and many more are used to help users ease many tasks such as looking up the weather, making a note and setting a remainder. Many a times, people want to create much more than that, like an app or a website. Now with this open source application, we enable virtual assistants to do just that.""",
      long_description = read('README.md'),

      url = "https://github.com/Maestorme/SoYouThinkYouCanWebpage",

      authors = "Karthick Shankar & Rahul Kartick",
      author_email = "maestorme@gmail.com",

      packages = find_packages(),

      dependency_links = [
           "http://people.csail.mit.edu/hubert/pyaudio/packages/pyaudio-0.2.8.tar.gz#egg=pyaudio",
      ],
      install_requires = [
           "pyaudio",
           "scikits.samplerate",
           "requests>=1.2.0",
           "pynput",
      ],

      classifiers = [
           'Development Status :: 4 - Beta',
           'Programming Language :: Python',
           'Intended Audience :: Developers',
           'Environment :: Console',
      ],

)
