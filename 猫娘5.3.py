import tkinter as tk
import os
from tkinter import ttk
from tkinter import filedialog
import openai
import json
import datetime
import atexit
import tiktoken
import unicodedata

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

if os.path.isfile('api_key.json'):
    # 读取 API 密钥
    with open('api_key.json') as f:
        data = json.load(f)
        openai.api_key = data['api_key']
else:
    # 提示用户输入 API 密钥
    print('请先在 api_key.json 文件中配置 API 密钥')
    exit()

# 默认tokens=0
total_tokens = 0

class App:

    # 主窗体
    def __init__(self, master):
        self.master = master
        master.title("ChatGPT GUI")
        master.geometry("800x600")
        root.minsize(667, 494)

        # 创建输入框和标签
        self.label = tk.Label(master, text="Enter a main message:")
        self.label.grid(row=0, column=0, sticky="N", padx=10, pady=10,columnspan=2)

        # 初始化 role 和 content 的列表
        self.roles = []
        self.contents = []       
        
        # 创建一个新的 frame
        self.table_frame = ttk.Frame(master)
        self.table_frame.grid(row=1, column=0, sticky="WESN", padx=10, pady=10)
        master.columnconfigure(0, weight=2)
        master.rowconfigure(1, weight=1)

        # 创建表格
        self.tree = ttk.Treeview(self.table_frame, selectmode="extended", columns=( "column1", "column2", "column3"), show="headings",height=15)
        self.tree.heading("#1", text="TKs")
        self.tree.heading("#2", text="Role")
        self.tree.heading("#3", text="Content")
        self.tree.column("#1", width=40,stretch=False)
        self.tree.column("#2", width=60,stretch=False)
        self.tree.column("#3", width=500, stretch=True)
        self.tree.tag_configure('user', background='#F0E68C')
        self.tree.tag_configure('assistant', background='#ADD8E6')
        self.tree.tag_configure('selected', background='#00008B')
        self.tree.grid(row=0, column=0, sticky="WE",rowspan=5)
        self.table_frame.columnconfigure(0, weight=1)
        self.table_frame.rowconfigure(0,weight=1)

        self.roles = []
        self.contents = []
        self.check_vars = [] 
        self.TKs = []

        # 创建表格
        scroBar = tk.Scrollbar(self.table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroBar.set)
        scroBar.grid(row=0, column=1, sticky="E",rowspan=5)
        
        # 让表格变成可编辑状态
        self.tree.bind("<Double-1>", self.edit_cell)
        
        #选择相关状态
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # 创建自定义样式
        style = ttk.Style()
        style.configure("Custom.Treeview", bordercolor="black", borderwidth=10, highlightthickness=1, bd=1, font=('Helvetica', 10), background="#ECECEC")
        style.configure("Custom.Treeview.Heading", background="#404040", foreground="black", font=('Helvetica', 10, 'bold'))

        # 映射样式到特定状态
        style.map("Custom.Treeview", background=[("selected", "#0078D7")], foreground=[("selected", "white")])
        style.map("Custom.Treeview", background=[("disabled", "#FDFDFD"), ("readonly", "#FDFDFD")], foreground=[("disabled", "#FDFDFD"), ("readonly", "#FDFDFD")])

        # 将样式应用于Treeview
        self.tree.config(style="Custom.Treeview")

        # 创建一个新的 frame
        row_button_frame = ttk.Frame(master)
        row_button_frame.grid(row=1, column=1, sticky="NE",rowspan=5)
        master.columnconfigure(1,minsize=self.table_frame.winfo_reqwidth())

        # 创建VAR对象
        self.total_tokens_var = tk.StringVar()
        self.total_tokens_var.set(f"Total tokens: {total_tokens}\nCharge: {total_tokens/500000}$")

        # 显示 total_tokens
        self.total_tokens_label = tk.Label(row_button_frame, textvariable=self.total_tokens_var)
        self.total_tokens_label.grid(row=0, column=2, padx=5, pady=5, sticky="E")

        # 添加一个 'Add Row' 按钮
        add_row_button = tk.Button(row_button_frame, text="Add Row", width=15, command=self.add_row)
        add_row_button.grid(row=1, column=2, padx=5, pady=5, sticky="E")

        # 添加一个 'Delete Row' 按钮
        delete_row_button = tk.Button(row_button_frame, text="Delete Row",width=15, command=self.delete_row)
        delete_row_button.grid(row=2, column=2, padx=5, pady=5,sticky="E")

        # 创建导出按钮
        self.export_button = tk.Button(row_button_frame, text="导出", width=15, command=self.export_data)
        self.export_button.grid(row=3, column=2, padx=5, pady=5,sticky="E")

        # 创建导入按钮
        self.import_button = tk.Button(row_button_frame, text="导入", width=15, command=self.import_data)
        self.import_button.grid(row=4, column=2, padx=5, pady=5, sticky="E")

        # 创建一个新的 frame
        sys_frame = ttk.Frame(master)
        sys_frame.grid(row=2, column=0 ,sticky="WE",columnspan=2)
        master.columnconfigure(0, weight=1)

        # 创建 system message 的文本框
        self.encode_num_var = tk.StringVar(value="System Content: [0]")
        self.system_content_label = tk.Label(sys_frame, width=20, textvariable=self.encode_num_var)
        self.system_content_label.grid(row=0, column=0, sticky="N")
        self.system_content_text = tk.Text(sys_frame, height=6, width=100)
        self.system_content_text.grid(row=1, column=0, columnspan=2, sticky="WE", padx=(10,10), pady=(0,10))
        self.system_content_text.bind("<KeyRelease>", self.encode_text)  # 绑定编码操作到 KeyRelease 事件
        sys_frame.columnconfigure(0, weight=1)
        sys_frame.rowconfigure(1, weight=1)

        # 创建一个新的frame并放置在 parameter_frame 中，用于放置 temperature、max_token、frequency_penalty 和 presence_penalty 的标签和文本框
        parameter_input_frame = ttk.Frame(master)
        parameter_input_frame.grid(row=3, column=0, sticky="N",columnspan=2)
        
        # temp和token的容器
        parameter_temperature_frame = ttk.Frame(parameter_input_frame)
        parameter_temperature_frame.grid(row=0, column=0, sticky="N",columnspan=2)

        # 创建文本框以设置temperature参数
        self.temp_label = tk.Label(parameter_temperature_frame, text="随机参数:",width=15)
        self.temp_label.grid(row=0, column=0, sticky="w")

        self.temperature_var = tk.DoubleVar(value=0.7)
        self.temperature = tk.Scale(parameter_temperature_frame, width=15, from_=0, to=2.0, resolution=0.1, orient="horizontal", variable=self.temperature_var)
        self.temperature.grid(row=0, column=1, sticky="w")
        self.temperature_entry = tk.Entry(parameter_temperature_frame, width=15, textvariable=self.temperature_var)
        self.temperature_entry.grid(row=0, column=2, sticky="w")
        
        # 创建文本框以设置token参数
        self.max_token_label = tk.Label(parameter_temperature_frame, text="回答长度：",width=15)
        self.max_token_label.grid(row=0, column=3, sticky="w")

        self.max_token_var = tk.IntVar(value=50)
        self.max_token_entry = tk.Scale(parameter_temperature_frame, width=15, from_=1, to=1000, resolution=1, orient="horizontal", variable=self.max_token_var)
        self.max_token_entry.grid(row=0, column=4, sticky="w")
        self.max_token_entry = tk.Entry(parameter_temperature_frame, width=15, textvariable=self.max_token_var)
        self.max_token_entry.grid(row=0, column=5, sticky="w")
        
        # f和p的容器
        parameter_freq_frame = ttk.Frame(parameter_input_frame)
        parameter_freq_frame.grid(row=1, column=0, sticky="N")

        # 创建文本框以设置frequency_penalty参数
        self.freq_penalty_label = tk.Label(parameter_freq_frame, text="语句复读惩罚:",width=15)
        self.freq_penalty_label.grid(row=0, column=0, sticky="w")
        self.freq_penalty_var = tk.DoubleVar(value=1.5)
        self.freq_penalty_entry = tk.Scale(parameter_freq_frame, width=15, from_=-2.0, to=2.0, resolution=0.1, orient="horizontal", variable=self.freq_penalty_var)
        self.freq_penalty_entry.grid(row=0, column=1, sticky="w")
        self.freq_penalty_entry = tk.Entry(parameter_freq_frame, width=15, textvariable=self.freq_penalty_var)
        self.freq_penalty_entry.grid(row=0, column=2, sticky="w")

        # 创建文本框以设置presence_penalty参数
        self.pres_penalty_label = tk.Label(parameter_freq_frame, text="话题复读惩罚:",width=15)
        self.pres_penalty_label.grid(row=0, column=3, sticky="w")
        self.pres_penalty_var = tk.DoubleVar(value=2.0)
        self.pres_penalty_entry = tk.Scale(parameter_freq_frame, width=15, from_=-2.0, to=2.0, resolution=0.1, orient="horizontal", variable=self.pres_penalty_var)
        self.pres_penalty_entry.grid(row=0, column=4, sticky="w")
        self.pres_penalty_entry = tk.Entry(parameter_freq_frame, width=15, textvariable=self.pres_penalty_var)
        self.pres_penalty_entry.grid(row=0, column=5, sticky="w")
        
        # 创建一个新的frame并放置在主窗口中，用于放置发送消息按钮
        button_frame = ttk.Frame(master)
        button_frame.grid(row=4, column=0,sticky="S",pady=(0,10),columnspan=2)

        # 创建发送消息按钮
        self.send_button = tk.Button(master, text="Send Message", command=self.send_message)
        self.send_button.grid(row=0, column=0, in_=button_frame)

        # 注册开关事件
        self.start_time = datetime.datetime.now()
        atexit.register(self.on_closing)

    # 返回system token数
    def encode_text(self,event):
        text = event.widget.get("1.0", "end-1c")  # 获取文本框中的内容
        encoded_num_var = len(encoding.encode(text))
        self.encode_num_var.set(f"System Content: [{encoded_num_var}]")

    # 用量记录
    def on_closing(self):

        end_time = datetime.datetime.now()
        run_time = end_time - self.start_time
        with open('log.txt', 'a') as f:
            f.write(f"start：{end_time} ")
            f.write(f"end：{run_time} " ) 
            f.write(f"tokens：{total_tokens} ")
            f.write(f"Charge：{total_tokens/500000}$\n")

    # 单击表
    def on_tree_select(self,event):
        clicked_item = event.widget.identify_row(event.y)
        self.selected_items = [] 
        
        for item in self.tree.selection():
            tags = self.tree.item(item, 'tags')  # 获取标签列表
            if 'selected' in tags:
                values = self.tree.item(item, "values")
                role = values[1]
                if role == "user":
                    tags = ['user']
                elif role == "assistant":
                    tags = ['assistant']
                else:
                    tags = []
                self.tree.item(item, tags=tags)  # 更新标签列表
            else:
                tags = ['selected']
                self.tree.item(item, tags=tags)  # 更新标签列表

    # 删除行
    def delete_row(self):
        items_to_delete = []
        for item in self.tree.get_children():
            tags = self.tree.item(item, "tags")
            if "selected" in tags:
                items_to_delete.append(item)

        if not items_to_delete:
            if self.tree.get_children():
                last_item = self.tree.get_children()[-1]
                self.tree.delete(last_item)
            else:
                pass #如果列表为空,什么也不做
        else:
            while items_to_delete:
                item = items_to_delete.pop(0)
                self.tree.delete(item)

    # 添加行
    def add_row(self):
        # 在 roles 和 contents 列表中添加空值
        self.TKs.append(0)
        self.roles.append("user")
        self.contents.append("")

        # 在表格中插入新行并为其添加标签
        index = len(self.tree.get_children()) + 1
        values = (self.TKs[-1],self.roles[-1], self.contents[-1])
        self.check_vars.append(tk.BooleanVar())
        item = self.tree.insert("", "end", text=str(index), values=values, tags=("user"))

    # 双击表
    def edit_cell(self, event):
        for item in self.tree.selection():
            # 获取选择的item中的信息
            item_text = self.tree.item(item, "values")
            column = self.tree.identify_column(event.x)
            row = self.tree.identify_row(event.y)

            # 获取被编辑的单元格索引
            cell_index = int(column.replace("#", "")) - 1


            # 创建一个顶层窗口用于编辑
            edit_window = tk.Toplevel(self.master)

            # 将窗口置于前台
            edit_window.lift()

            # 基于所选行和列插入逐字稿以便编辑
            edit_box = tk.Text(edit_window, width=40, height=3)
            edit_box.insert(tk.END, item_text[cell_index])

            # 定义提交编辑的回调
            def submit_edit():
                new_value = edit_box.get("1.0", tk.END).strip()
                
                # 更新TKs
                encoded_content = len(encoding.encode(self.tree.item(item, "values")[2]))
                self.tree.set(item, "#1", encoded_content)

                # 更新树上的值并销毁此窗口
                self.tree.set(item, f"#{cell_index+1}", new_value)
                edit_window.destroy()
                # 修改背景色
                new_role = self.tree.item(item, "values")[1]
                if new_role == "user":
                    self.tree.item(item, tags=("user",))
                else:
                    self.tree.item(item, tags=("assistant",))
                
            # 创建提交编辑的按钮
            submit_button = tk.Button(edit_window, text="Submit", command=submit_edit)

            # 在窗口中排列控件
            edit_box.pack()
            submit_button.pack()
            # 让 window 具有 keyboard focus and grab 鼠标，这样它将成为事件处理程序
            edit_window.focus_set()
            edit_window.grab_set()
            edit_window.wait_window()

    # send message
    def send_message(self):
        global total_tokens
        # 获取已存在的对话信息和系统内容
        message_M = [{"role": self.tree.item(row, "values")[1], "content": self.tree.item(row, "values")[2]} for row in self.tree.get_children()]
        system_content = self.system_content_text.get("1.0", tk.END).strip()

        # 检查每个消息的 role 字段是否设置为有效值，如果不是，则将其设置为 "assistant"
        for m in message_M:
            # 检查是否存在空字符串并删除
            if not m["content"].strip():
                message_M.remove(m)
            # 检查角色是否被正确分配
            if m["role"] not in ["system", "assistant", "user"]:
                m["role"] = "assistant"

        # 拼接 prompt
        prompt = []
        prompt.append({"role": "system", "content": system_content})
        for m in message_M:
            role = m["role"] 
            content = m["content"]
            prompt.append({"role": role, "content": content})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            temperature = float(self.temperature.get()),
            max_tokens= int(self.max_token_entry.get()),
            frequency_penalty= float(self.freq_penalty_entry.get()),
            presence_penalty= float(self.pres_penalty_entry.get()),
            timeout=7
        )

        # 获取 GPT-3 返回的系统内容和新对话
        response_dict = json.loads(str(response))
        usage = response_dict["usage"]
        current_tokens = usage["total_tokens"]
        choices = response_dict["choices"]
        if choices:
            TKs = usage["completion_tokens"]
            role = choices[0]["message"]["role"]
            content = choices[0]["message"]["content"]
            content = content.lstrip("\n")
            content = content.strip()
            content = content.replace('\n', '')
            content = content.replace(' ', '')
            content = unicodedata.normalize('NFKC', content)
            new_messages = [{"TKs": TKs, "role": role, "content": content}]
            total_tokens += int(current_tokens)
            self.total_tokens_var.set(f"Total tokens: {total_tokens}\nCharge: {total_tokens/500000}$")
        else:
            new_messages = []
        
        # 更新 messages 列表
        for message in new_messages:
            TKs, role, content = message["TKs"], message["role"], message["content"]
            message_M.append({"TKs": str(TKs).strip(), "role": role.strip(), "content": content.strip()})

        # 更新表格
        if len(self.tree.get_children()) == 0:
            index = 1
            values = (new_messages[0]["TKs"], new_messages[0]["role"], new_messages[0]["content"])
            item = self.tree.insert("", "end", text=str(index), values=values)
        else:
            index = len(self.tree.get_children()) + 1
            values = (new_messages[0]["TKs"], new_messages[0]["role"], new_messages[0]["content"])
            item = self.tree.insert("", "end", text=str(index), values=values) 
            
        new_role = self.tree.item(item, "values")[0]
        if new_role == "user":
            self.tree.item(item, tags=("user",))
        else:
            self.tree.item(item, tags=("assistant",)) 
        
        for item in self.tree.selection():
            tags = self.tree.item(item, 'tags')  # 获取标签列表
            if 'selected' in tags:
                values = self.tree.item(item, "values")
                role = values[1]
                if role == "user":
                    tags = ['user']
                elif role == "assistant":
                    tags = ['assistant']
                else:
                    tags = []
                self.tree.item(item, tags=tags)  # 更新标签列表
                self.selected_items.remove(item)  # 从selected_items列表中移除该行
            else:
                tags = tags
                self.tree.item(item, tags=tags)  # 更新标签列表
        
        # 输出所有信息
        print(message_M)
        print(int(self.max_token_entry.get()))
        print(usage)

    # 输出JSON
    def export_data(self):
        # 获取当前时间
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # 构造要保存的数据
        data = []
        for row_id in self.tree.get_children():
            TKs = self.tree.item(row_id, "values")[0] 
            role = self.tree.item(row_id, "values")[1]
            content = self.tree.item(row_id, "values")[2]
            # 解码 content 字符串
            content = content.encode('utf-8').decode('utf-8')
            data.append({"TKs": TKs, "role": role, "content": content})
            with open(f"{current_time}.json", "w") as f:
                json.dump(data, f)
        # 将每个列表元素后面添加一个换行符
        txt_str = ""
        for item in data:
            txt_str += f"{item['role']}: {item['content']}\n"
        # 保存为 txt 文件
        with open(f"{current_time}.txt", "w") as f:
            f.write(txt_str)
        print(f"Exported data to {current_time}.txt")


    # 导入
    def import_data(self):
    # 打开文件对话框，选择要导入的文件
        file_path = filedialog.askopenfilename(filetypes=[('JSON files', '*.json')])
        if file_path:
            with open(file_path, 'r') as f:
                data = json.load(f)
                for i, item in enumerate(data):
                    TKs = item["TKs"]
                    role = item["role"]
                    content = item["content"]
                    if role == "user":
                        tags = ['user']
                    elif role == "assistant":
                        tags = ['assistant']
                    else:
                        tags = []
                    self.tree.insert("", "end", values=( TKs, role, content), tags=tags)

    # 更新表格高度
    def update_row_heights(self):
        for row_id in self.tree.get_children():
            cell_heights = []
            for col in range(2):
                cell_content = self.tree.set(row_id, column=col)
                cell_lines = cell_content.split('\n')
                cell_height = len(cell_lines)
                cell_heights.append(cell_height)
            max_cell_height = max(cell_heights)
            self.tree.rowconfigure(row_id, minsize=max_cell_height * 20)

root = tk.Tk()
my_app = App(root)
root.mainloop()