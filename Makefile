PHONY: tailwindcss-watch

tailwindcss-watch:
	tailwindcss -i ./styles/main.css -o ./static/css/main.css --watch

tailwindcss-build:
	tailwindcss -i ./styles/main.css -o ./static/css/main.css --minify
