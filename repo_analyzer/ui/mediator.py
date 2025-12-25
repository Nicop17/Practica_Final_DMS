from flask import render_template
from typing import Dict, Any, Tuple, Optional
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import ConfigSingleton

class InputComponent:
    def parse(self, form: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        repo_url = form.get("repo_url", "").strip()
        if not repo_url:
            return None, "Por favor, introduzca una URL válida del repositorio."
        return repo_url, None

    def context(self, error: Optional[str] = None) -> Dict[str, Any]:
        return {"input_error": error}

class OptionsComponent:
    def parse(self, form: Dict[str, Any]) -> Dict[str, Any]:
        force = form.get("force") == "on"
        try:
            default_window = ConfigSingleton.get_instance().duplication_window
        except Exception:
            default_window = 4

        try:
            val = form.get("dup_window")
            if val is None or val == "":
                dup_window = default_window
            else:
                dup_window = int(val)
        except ValueError:
            dup_window = default_window
            
        return {"force": force, "dup_window": dup_window}

    def context(self, parsed_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            default_window = ConfigSingleton.get_instance().duplication_window
        except Exception:
            default_window = 4
        defaults = {"force": False, "dup_window": default_window}
        return {"options": parsed_options or defaults}

class OutputComponent:
    def prepare(self, result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not result:
            return {"show_output": False}
        
        summary = result.get("summary", {})
        
        return {
            "show_output": True,
            "repo": result.get("repo", ""),
            "analyzed_at": result.get("analyzed_at", ""),
            "from_cache": result.get("_from_cache", False),
            "forced": result.get("forced", False),
            "num_files": summary.get("num_files", 0),
            "total_lines": summary.get("total_lines", 0),
            "avg_cc": summary.get("avg_cc", 0.0),
            "maintainability": summary.get("maintainability_index", 0.0),
            "duplication": summary.get("duplication", 0.0),
        }

class HistoryComponent:
    def get_entries(self, subject) -> Dict[str, Any]:
        try:
            entries = subject.list_analyses()
        except Exception:
            entries = []
        return {"history": entries}

class UIMediator:
    def __init__(self, subject):
        self.subject = subject

    def show_index(self):
        input_c = InputComponent()
        options_c = OptionsComponent()
        output_c = OutputComponent()
        history_c = HistoryComponent()

        ctx = {}
        ctx.update(input_c.context())
        ctx.update(options_c.context())
        ctx.update(output_c.prepare(None))
        ctx.update(history_c.get_entries(self.subject))
        return render_template("index.html", **ctx)

    def handle_analyze(self, form: Dict[str, Any]):
        input_c = InputComponent()
        options_c = OptionsComponent()
        output_c = OutputComponent()
        history_c = HistoryComponent()

        repo_url, error = input_c.parse(form)
        
        if error:
            ctx = {}
            ctx.update(input_c.context(error))
            ctx.update(options_c.context()) 
            ctx.update(output_c.prepare(None))
            ctx.update(history_c.get_entries(self.subject))
            return render_template("index.html", **ctx)

        opts = options_c.parse(form)

        try:
            result = self.subject.peticion(
                repo_url, 
                force=opts.get("force", False),
                options=opts
            )
        except Exception as e:
            error_msg = f"Error durante el análisis: {str(e)}"
            ctx = {}
            ctx.update(input_c.context(error_msg))
            ctx.update(options_c.context(opts))
            ctx.update(output_c.prepare(None))
            ctx.update(history_c.get_entries(self.subject))
            return render_template("index.html", **ctx)

        out_ctx = output_c.prepare(result)
        hist_ctx = history_c.get_entries(self.subject)

        ctx = {}
        ctx.update(input_c.context())
        ctx.update(options_c.context(opts))
        ctx.update(out_ctx)
        ctx.update(hist_ctx)
        return render_template("index.html", **ctx)
