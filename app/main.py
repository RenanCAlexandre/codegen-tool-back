from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

from converters.base_generator import BaseGenerator
from converters.bootstrap_generator import BootstrapGenerator
from converters.tailwind_generator import TailwindGenerator

app = Flask(__name__)
CORS(app, origins=["*", "chrome-extension://*"])


base_engine = BaseGenerator()
bootstrap_engine = BootstrapGenerator()
tailwind_engine = TailwindGenerator()

latest_code_result = {
    "base": "",
    "bootstrap": "",
    "tailwind": ""
}

@app.route("/")
def index():
    return render_template("index.html",
        base_code=latest_code_result["base"],
        bootstrap_code=latest_code_result["bootstrap"],
        tailwind_code=latest_code_result["tailwind"]
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/convert", methods=["POST"])
def convert():
    try:
        data = request.get_json(force=True)

        html_raw = data.get("element_outer_html") or ""
        if not html_raw.strip():
            return jsonify({"ok": False, "error": "Missing 'element_outer_html'"}), 400

        base_html = base_engine.generate(html_raw)
        bootstrap_html = bootstrap_engine.generate(base_html)
        tailwind_html = tailwind_engine.generate(base_html)

        return jsonify({
            "ok": True,
            "source": {
                "page_url": data.get("page_url", ""),
                "clicked_selector": data.get("clicked_selector", "")
            },
            "code": {
                "base": base_html,
                "bootstrap": bootstrap_html,
                "tailwind": tailwind_html
            },
            "meta": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "engine_versions": {
                    "base": "1.0.0",
                    "bootstrap": "1.0.0",
                    "tailwind": "1.0.0"
                }
            }
        }), 200


    except Exception as e:

        import traceback

        print("ERROR in /api/convert:", str(e))

        traceback.print_exc()

        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/view", methods=["POST"])
def set_view_data():
    global latest_code_result
    data = request.get_json()
    latest_code_result["base"] = data.get("base", "")
    latest_code_result["bootstrap"] = data.get("bootstrap", "")
    latest_code_result["tailwind"] = data.get("tailwind", "")
    return jsonify({"ok": True})

@app.route("/api/latest-code", methods=["GET"])
def latest_code():
    return jsonify({
        "base": latest_code_result["base"],
        "bootstrap": latest_code_result["bootstrap"],
        "tailwind": latest_code_result["tailwind"]
    })


if __name__ == "__main__":
    app.run(debug=True)
