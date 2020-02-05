help:           ## Show this help.
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

install:  ## 安装
	pip install -r requirements.txt

run:  ## 运行
	python src/kouzhao.py
