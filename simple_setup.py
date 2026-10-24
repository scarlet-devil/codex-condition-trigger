"""Three-field Tk setup. --simulate uses only an isolated, explicit fake transport."""

import argparse
import json
import math
import os
import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk

import trigger as tr
from simple_catalog import read_catalog
from simple_controller import Controller, saved_rules

CONDITIONS = {
    "新内容写入稳定后": "new_content_stable",
    "出现 READY 且内容稳定后": "ready_content_stable",
}
DEFAULT_INSTRUCTION = "Review the new material and return a concise result."


def summary(c, title, preview_count=None):
    return (
        f"对话：{title}  ·  {c['thread_id'][-8:]}\n项目：{c['expected_cwd']}\n"
        f"文件夹：{c['input_dir']}（递归扫描子文件夹）\n"
        f"包含：{', '.join(c['include'])}；排除：{', '.join(c['exclude'])}\n"
        f"稳定期：{c['settle_seconds']} 秒；READY：{c.get('ready_file') or '不需要'}；"
        f"初始文件：{'忽略' if c['initial_files'] == 'ignore' else '处理'}\n"
        f"指令：{c.get('task_instruction', DEFAULT_INSTRUCTION)}\n"
        f"预览文件数：{preview_count if preview_count is not None else '已保存规则'}；启用时会重新扫描并显示实际数量。"
    )


class App:
    def __init__(
        self,
        root,
        controller,
        catalog_path,
        *,
        simulation_input=None,
        fake=None,
        evidence_path=None,
    ):
        self.root = root
        self.c = controller
        self.catalog_path = catalog_path
        self.simulation_input = simulation_input
        self.fake = fake
        self.evidence_path = evidence_path
        self.started = time.monotonic()
        self.trace = []
        self.queue = queue.Queue()
        self.io_threads = []
        self.catalog_generation = 0
        self.catalog_busy = False
        self.rows = {}
        self.selected = None
        self.initializing = True
        self.last_refresh = 0
        self.last_summary = None
        root.title("条件触发器 · G2 模拟" if fake else "条件触发器")
        root.geometry("940x830")
        root.minsize(800, 730)
        root.protocol("WM_DELETE_WINDOW", self.close)
        pane = ttk.Frame(root, padding=16)
        pane.pack(fill="both", expand=True)
        ttk.Label(
            pane, text="条件触发器", font=("Microsoft YaHei UI", 17, "bold")
        ).pack(anchor="w")
        ttk.Label(
            pane,
            text="模拟模式：真实本地扫描，fake 传输，不连接 Codex、不发送模型任务。"
            if fake
            else "选择文件夹、触发条件和目标对话。启用后保留原对话中的工作上下文。",
        ).pack(anchor="w", pady=(4, 12))
        fields = ttk.Frame(pane)
        fields.pack(fill="x")
        fields.columnconfigure(1, weight=1)
        self.folder = tk.StringVar()
        self.condition = tk.StringVar(value=next(iter(CONDITIONS)))
        self.search = tk.StringVar()
        self.settle = tk.StringVar(value="120")
        self.initial = tk.StringVar(value="忽略现有文件")
        self.instruction = tk.StringVar()
        self.edit_widgets = []
        ttk.Label(fields, text="文件夹").grid(row=0, column=0, sticky="w", padx=(0, 12))
        entry = ttk.Entry(fields, textvariable=self.folder)
        entry.grid(row=0, column=1, sticky="ew")
        self.edit_widgets.append(entry)
        pick = ttk.Button(fields, text="选择文件夹…", command=self.pick)
        pick.grid(row=0, column=2, padx=(8, 0))
        self.edit_widgets.append(pick)
        ttk.Label(fields, text="触发条件").grid(row=1, column=0, sticky="w", pady=10)
        conditions = ttk.Combobox(
            fields,
            textvariable=self.condition,
            values=list(CONDITIONS),
            state="readonly",
        )
        conditions.grid(row=1, column=1, columnspan=2, sticky="ew")
        self.edit_widgets.append(conditions)
        ttk.Label(pane, text="目标对话 · 可按名称或项目搜索").pack(anchor="w")
        searchrow = ttk.Frame(pane)
        searchrow.pack(fill="x", pady=5)
        search = ttk.Entry(searchrow, textvariable=self.search)
        search.pack(side="left", fill="x", expand=True)
        self.edit_widgets.append(search)
        self.catalog_button = ttk.Button(
            searchrow, text="刷新对话", command=self.catalog
        )
        self.catalog_button.pack(side="left", padx=(8, 0))
        self.edit_widgets.append(self.catalog_button)
        self.tree = ttk.Treeview(
            pane,
            columns=("name", "project", "updated", "id"),
            show="headings",
            height=4,
            selectmode="browse",
        )
        for key, label, width in [
            ("name", "名称", 180),
            ("project", "项目", 380),
            ("updated", "最近更新", 145),
            ("id", "区分标识", 95),
        ]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, minwidth=70)
        self.tree.pack(fill="x")
        self.tree.bind("<<TreeviewSelect>>", self.choose)
        bar = ttk.Scrollbar(pane, orient="horizontal", command=self.tree.xview)
        bar.pack(fill="x")
        self.tree.configure(xscrollcommand=bar.set)
        self.target_label = tk.StringVar(value="尚未选择对话")
        ttk.Label(pane, textvariable=self.target_label, wraplength=880).pack(
            anchor="w", pady=4
        )
        ttk.Button(
            pane, text="高级选项（稳定时间、初始文件、可选指令）", command=self.toggle
        ).pack(anchor="w", pady=5)
        self.advanced = ttk.Frame(pane)
        self.advanced.columnconfigure(1, weight=1)
        ttk.Label(self.advanced, text="稳定时间（秒）").grid(
            row=0, column=0, sticky="w"
        )
        settle = ttk.Entry(self.advanced, textvariable=self.settle, width=12)
        settle.grid(row=0, column=1, sticky="w")
        self.edit_widgets.append(settle)
        init = ttk.Combobox(
            self.advanced,
            textvariable=self.initial,
            values=("忽略现有文件", "处理现有文件"),
            state="readonly",
            width=18,
        )
        init.grid(row=0, column=2)
        self.edit_widgets.append(init)
        ttk.Label(self.advanced, text="可选指令").grid(
            row=1, column=0, sticky="w", pady=4
        )
        instruction = ttk.Entry(self.advanced, textvariable=self.instruction)
        instruction.grid(row=1, column=1, columnspan=2, sticky="ew")
        self.edit_widgets.append(instruction)
        self.summary_var = tk.StringVar(
            value="填写三项后预览。默认稳定期 120 秒，忽略启用前已有文件。"
        )
        self.summary_label = ttk.Label(
            pane, textvariable=self.summary_var, wraplength=880, justify="left"
        )
        self.summary_label.pack(fill="x", pady=8)
        actions = ttk.Frame(pane)
        actions.pack(fill="x", pady=5)
        self.buttons = {}
        for name, fn in [
            ("预览", self.preview),
            ("启用监听", self.c.enable),
            ("暂停", self.c.pause),
            ("恢复", self.c.resume),
            ("新规则", self.new),
            ("最小化", root.iconify),
            ("关闭", self.close),
        ]:
            button = ttk.Button(actions, text=name, command=lambda f=fn: self.action(f))
            button.pack(side="left", padx=(0, 6))
            self.buttons[name] = button
        saved = ttk.Frame(pane)
        saved.pack(fill="x", pady=4)
        ttk.Label(saved, text="本表单保存的规则").pack(side="left")
        self.saved = ttk.Combobox(saved, state="readonly")
        self.saved.pack(side="left", fill="x", expand=True, padx=7)
        ttk.Button(saved, text="读取规则", command=lambda: self.action(self.load)).pack(
            side="left"
        )
        self.status_var = tk.StringVar(value="尚未启用")
        ttk.Label(
            pane, textvariable=self.status_var, wraplength=880, justify="left"
        ).pack(fill="x", pady=8)
        self.error_var = tk.StringVar()
        ttk.Label(
            pane, textvariable=self.error_var, foreground="#a21b1b", wraplength=880
        ).pack(fill="x")
        if fake:
            demo = ttk.Frame(pane)
            demo.pack(fill="x", pady=6)
            ttk.Label(demo, text="合成试验操作：").pack(side="left")
            for name, fn in [
                ("写入 A", lambda: self.synthetic("A")),
                ("写入 B", lambda: self.synthetic("B")),
                ("结束模拟回合", self.fake.finish),
            ]:
                ttk.Button(demo, text=name, command=lambda f=fn: self.action(f)).pack(
                    side="left", padx=4
                )
        for var in (
            self.folder,
            self.condition,
            self.settle,
            self.initial,
            self.instruction,
        ):
            var.trace_add("write", lambda *_: self.dirty())
        self.search.trace_add("write", lambda *_: self.invalidate_catalog())
        self.initializing = False
        self.catalog()
        self.saved_entries = []
        self.refresh_saved()
        self.root.after(100, self.poll)

    def action(self, fn):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - report the worker or UI boundary error
            self.error_var.set(f"{type(exc).__name__}: {exc}")

    def toggle(self):
        if self.advanced.winfo_manager():
            self.advanced.pack_forget()
        else:
            self.advanced.pack(fill="x", before=self.summary_label)

    def pick(self):
        result = filedialog.askdirectory(
            parent=self.root,
            title="选择要监听的文件夹",
            initialdir=self.folder.get() or self.simulation_input or Path.home(),
            mustexist=True,
        )
        self.trace.append(
            {
                "event": "folder_picker",
                "chosen": bool(result),
                "elapsed": time.monotonic() - self.started,
            }
        )
        if result:
            self.folder.set(result)

    def dirty(self):
        if not self.initializing and self.c.config is None:
            self.c.update({})
            self.summary_var.set("配置已改变，请重新预览。")
            self.last_summary = None

    def invalidate_catalog(self):
        self.catalog_generation += 1

    def io(self, fn):
        t = threading.Thread(target=fn, name="simple-ui-metadata", daemon=False)
        self.io_threads.append(t)
        t.start()

    def catalog(self):
        if self.catalog_busy or self.c.config is not None:
            return
        self.catalog_busy = True
        self.catalog_generation += 1
        generation = self.catalog_generation
        search = self.search.get()

        def work():
            try:
                self.queue.put(
                    (
                        "catalog",
                        generation,
                        read_catalog(self.catalog_path, search=search),
                    )
                )
            except Exception as exc:  # noqa: BLE001 - report the worker or UI boundary error
                self.queue.put(("catalog_error", generation, str(exc)))

        self.io(work)

    def choose(self, _=None):
        if self.c.config is not None:
            return
        chosen = self.tree.selection()
        self.selected = self.rows.get(chosen[0]) if chosen else None
        self.target_label.set(
            self.selected["display_label"] if self.selected else "尚未选择对话"
        )
        self.dirty()

    def preview(self):
        if not self.selected:
            raise ValueError("请选择目标对话")
        settle = float(self.settle.get())
        if not math.isfinite(settle) or settle <= 0:
            raise ValueError("稳定时间必须为有限正数")
        form = {
            "folder": self.folder.get(),
            "condition": CONDITIONS[self.condition.get()],
            "selection": self.selected,
            "settle_seconds": settle,
            "initial_files": "ignore"
            if self.initial.get() == "忽略现有文件"
            else "process",
        }
        if self.instruction.get().strip():
            form["instruction"] = self.instruction.get().strip()
        self.c.update(form)
        self.c.preview()
        self.error_var.set("")

    def refresh_saved(self):
        def work():
            try:
                self.queue.put(("saved", 0, saved_rules(self.c.home)))
            except Exception as exc:  # noqa: BLE001 - report the worker or UI boundary error
                self.queue.put(("error", 0, str(exc)))

        self.io(work)

    def load(self):
        if self.saved.current() < 0:
            raise ValueError("请选择已保存规则")
        self.c.load(self.saved_entries[self.saved.current()]["path"])

    def new(self):
        self.c.new()
        self.last_summary = None
        self.dirty()
        self.refresh_saved()

    def synthetic(self, name):
        (Path(self.simulation_input) / (name + ".txt")).write_text(
            "Synthetic content " + name, encoding="utf8"
        )
        self.trace.append(
            {
                "event": "synthetic_write",
                "name": name,
                "elapsed": time.monotonic() - self.started,
            }
        )

    def close(self):
        self.trace.append(
            {"event": "close_requested", "elapsed": time.monotonic() - self.started}
        )
        self.c.close()

    def poll(self):
        while not self.queue.empty():
            kind, generation, value = self.queue.get_nowait()
            if kind.startswith("catalog"):
                self.catalog_busy = False
                if generation != self.catalog_generation:
                    continue
                if kind == "catalog_error":
                    self.error_var.set(value)
                    continue
                selected = self.selected["id"] if self.selected else None
                self.rows = {r["id"]: r for r in value}
                self.tree.delete(*self.tree.get_children())
                for r in value:
                    self.tree.insert(
                        "",
                        tk.END,
                        iid=r["id"],
                        values=(
                            r["display_name"],
                            r["cwd"],
                            datetime.fromtimestamp(r["updated_at"]).strftime(
                                "%m-%d %H:%M"
                            ),
                            r["short_id"],
                        ),
                    )
                if selected in self.rows:
                    self.tree.selection_set(selected)
                else:
                    self.selected = None
                    self.target_label.set("请选择目标对话")
                    self.dirty()
            elif kind == "saved":
                self.saved_entries = value
                self.saved["values"] = [r["label"] for r in value]
            else:
                self.error_var.set(value)
        while not self.c.events.empty():
            event = self.c.events.get_nowait()
            event["elapsed"] = time.monotonic() - self.started
            self.trace.append(event)
            if event["event"] == "baseline_committed":
                self.refresh_saved()
        v = self.c.view()
        p = v["preview"]
        c = v["config"]
        s = v["status"]
        if v["error"]:
            self.error_var.set(v["error"])
        if p and self.last_summary != p:
            self.summary_var.set(summary(p["config"], p["target_title"], p["files"]))
            self.last_summary = p
        elif c and not p and self.last_summary != c:
            self.summary_var.set(
                summary(
                    c,
                    self.selected["display_name"]
                    if self.selected and self.selected["id"] == c["thread_id"]
                    else "已保存对话",
                )
            )
            self.last_summary = c
        locked = c is not None or v["closing"]
        for widget in self.edit_widgets:
            widget.state(["disabled"] if locked else ["!disabled"])
        self.catalog_button.state(
            ["disabled"] if locked or self.catalog_busy else ["!disabled"]
        )
        for label in ("预览", "启用监听", "恢复", "新规则"):
            disable = (
                v["closing"]
                or v["command_busy"]
                or (label in ("启用监听", "恢复", "新规则") and v["alive"])
                or (label == "预览" and locked)
            )
            self.buttons[label].state(["disabled"] if disable else ["!disabled"])
        names = {
            "listening": "监听中",
            "starting": "规则已启用，等待首次扫描",
            "health_attention": "监听进度需检查",
            "enabled_no_worker": "规则已启用，本窗口没有运行中的监听器",
            "stopped": "已暂停 / 未运行",
            "failed": "监听异常退出",
        }
        mode = (
            "正在停止，等待读写、连接和监听线程释放…"
            if v["closing"]
            else "正在暂停，等待监听线程释放…"
            if v["pausing"]
            else "正在初始化 / 查询…"
            if v["command_busy"]
            else names.get(s.get("monitoring"), "尚未开始扫描")
        )
        health = s.get("watcher", {})
        batches = s.get("batches", [])
        descriptions = []
        for b in batches[:4]:
            state = b["state"]
            desc = (
                "投递结果不明，等待核对"
                if state in ("sending", "uncertain")
                else "回合结束，业务未验收"
                if b["exact_terminal"]
                else "已接受 / 正在执行"
                if b["native_acceptance"]
                else "等待连接或目标空闲"
            )
            descriptions.append(
                f"{b['id'][:8]}：{desc}；执行结果 {b['execution_outcome']}"
            )
        resource = {
            "batch_capacity": "批次上限：停止形成新批，已有批仍推进",
            "state_capacity": "容量上限：停止形成新批和投递",
        }.get(s.get("resource_reason"), "")
        self.status_var.set(
            f"{mode}\n实际初始文件：{s.get('initial_files', '未提交')}；待处理批次：{s.get('backlog', 0)}；进度新鲜度：{health.get('freshness', 'unknown')}\n连接 / 等待：{health.get('dispatch_result', '尚未查询')}；扫描：{health.get('scan_result', '未发生')}\n"
            + "\n".join(descriptions)
            + ("\n" + resource if resource else "")
        )
        now = time.monotonic()
        if not v["closing"] and now - self.last_refresh > 0.5:
            self.c.refresh()
            self.last_refresh = now
        if v["closed"] and not any(t.is_alive() for t in self.io_threads):
            if self.evidence_path:
                result = {
                    "schema": 1,
                    "simulation": bool(self.fake),
                    "events": self.trace,
                    "elapsed_seconds": now - self.started,
                    "workers_released": True,
                    "controller_error": v["error"],
                    "fake_sent": self.fake.sent if self.fake else [],
                    "fake_targets": self.fake.targets if self.fake else [],
                    "real_ipc_calls": 0 if self.fake else None,
                    "model_tasks": 0 if self.fake else None,
                }
                tr.atomic_write(
                    Path(self.evidence_path),
                    (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode(),
                )
            self.root.destroy()
            return
        self.root.after(100, self.poll)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--simulate",
        type=Path,
        help="new isolated fixture directory; explicit fake transport",
    )
    args = parser.parse_args()
    fake = None
    input_dir = None
    evidence = None
    if args.simulate:
        from experimental.simple_form_fake import prepare

        catalog, input_dir, fake = prepare(args.simulate)
        tr.target_registry_root = lambda: args.simulate.resolve() / "registry"
        home = args.simulate.resolve() / "rules"
        evidence = args.simulate.resolve() / "ui-evidence.json"
    else:
        catalog = (
            Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
            / "state_5.sqlite"
        )
        home = tr.target_registry_root() / "simple-rules"
    controller = Controller(
        home,
        adapter_factory=fake.factory if fake else None,
        simulation=bool(fake),
        dispatch_interval=0.1 if fake else 10,
    )
    root = tk.Tk()
    App(
        root,
        controller,
        catalog,
        simulation_input=input_dir,
        fake=fake,
        evidence_path=evidence,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
