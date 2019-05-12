build:
	python setup.py build_ext --inplace

clean:
	rm -rf ./build ./dist \
		   ./octobot_websockets/*.so ./octobot_websockets/*.pyc \
		   ./octobot_websockets/*.c \
		   ./*.egg-info

install: build
	python setup.py install

test: install
	pytest -rw tests
