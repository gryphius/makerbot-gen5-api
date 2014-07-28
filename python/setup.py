from distutils.core import setup

setup(name = "makerbot-gen5-api",
    version = "0.1",
    description = "Python API for makerbot 5th generation 3D printers",
    author = "J. Rebeiro, O. Schacher",
    url='https://github.com/gryphius/makerbot-gen5-api',
    download_url='https://github.com/gryphius/makerbot-gen5-api/tarball/master',
    author_email = "oli@wgwh.ch",
    #requires = [''], #TODO add image decoding library here?
    packages = ['makerbotapi'],
    long_description = """Python API for makerbot 5th generation 3D printers""" ,
    data_files=[
                # TODO: storage for auth tokens
                ],
      classifiers=[
	  'Topic :: Software Development :: Libraries',
	  'Topic :: Printing',
          'Development Status :: 2 - Pre-Alpha',
          'Programming Language :: Python',
          ],
)

        
        
        