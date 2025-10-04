# ================= IMPORTS DAS BIBLIOTECAS QUE EU PRECISO =================
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.window import Window
import datetime
import json
import os

# ================= CONSTANTES GLOBAIS DO MEU APLICATIVO =================

# Aqui eu defino o nome do arquivo onde vou salvar os dados dos produtos.
DATA_FILE = "produtos.json"
# Para o meu sistema de carregamento progressivo, defini que vou carregar 30 produtos por vez.
LOTE_DE_CARGA = 30


# ================= FUNÇÕES PARA CUIDAR DOS DADOS (ARQUIVO JSON) =================

def carregar_produtos():
    # Criei esta função para carregar os produtos do meu arquivo JSON.
    if os.path.exists(DATA_FILE):
        try:
            # Se o arquivo existe, eu abro, leio os dados e os converto de volta para o formato que preciso.
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Tenho que converter as datas, que estão como texto no arquivo, para objetos de data do Python.
            for p in data:
                p["data_validade"] = datetime.datetime.strptime(p["data_validade"], "%Y-%m-%d").date()
                if p.get("data_exclusao"):
                    p["data_exclusao"] = datetime.datetime.strptime(p["data_exclusao"], "%Y-%m-%d").date()
            return data
        except (json.JSONDecodeError, TypeError):
            # Se o arquivo estiver corrompido ou algo der errado, eu carrego uma lista padrão.
            return _get_default_produtos()
    else:
        # Se o arquivo não existir (primeira vez usando o app), eu chamo a função que cria uma lista inicial.
        return _get_default_produtos()


def _get_default_produtos():
    # Esta é a lista de produtos que eu defini para aparecer quando o app é aberto pela primeira vez, como teste.
    hoje = datetime.date.today()
    return [
        {"nome": "Barrinha de Nuts", "data_validade": hoje + datetime.timedelta(days=10), "possui_troca": False},
        {"nome": "Tofu Defumado 250g", "data_validade": hoje + datetime.timedelta(days=25), "possui_troca": True},
        {"nome": "Kombuchá de Guaraná", "data_validade": hoje + datetime.timedelta(days=3), "possui_troca": False},
        {"nome": "Pipoca Doce", "data_validade": hoje + datetime.timedelta(days=-2), "possui_troca": False},
        {"nome": "Pé de Moleque Zero", "data_validade": hoje + datetime.timedelta(days=7), "possui_troca": False},
    ]


def salvar_todos_produtos(app_instance):
    # Esta função é crucial: ela pega todos os produtos (da lista principal e da lixeira) e salva no arquivo JSON.
    lista_para_salvar = []

    # Primeiro, eu pego os produtos que estão na lista principal.
    for card in app_instance.root.ids.lista_produtos.children:
        item = {
            "nome": card.nome,
            "data_validade": datetime.datetime.strptime(card.validade, "%d/%m/%Y").date().isoformat(),
            "possui_troca": card.troca == "Sim",
            "vendido": card.vendido,
            "alerta_original": card.alerta_original,
            "excluido": False,
            "data_exclusao": None
        }
        lista_para_salvar.append(item)

    # Depois, eu faço o mesmo para os produtos que estão na lixeira, marcando que estão excluídos.
    for card in app_instance.root.ids.lista_excluidos.children:
        item = {
            "nome": card.nome,
            "data_validade": datetime.datetime.strptime(card.validade, "%d/%m/%Y").date().isoformat(),
            "possui_troca": card.troca == "Sim",
            "vendido": card.vendido,
            "alerta_original": card.alerta_original,
            "excluido": True,
            "data_exclusao": card.data_exclusao.isoformat() if card.data_exclusao else None
        }
        lista_para_salvar.append(item)

    # Finalmente, eu escrevo a lista completa no arquivo JSON.
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(lista_para_salvar, f, indent=4)


# ================== CLASSE PARA O CARD DE PRODUTO ==================

class ProductCard(BoxLayout):
    # Aqui eu defino as propriedades que cada card de produto vai ter. O Kivy vai atualizar a interface quando elas mudarem.
    nome = StringProperty("")
    validade = StringProperty("")
    dias = StringProperty("")
    troca = StringProperty("")
    alerta = StringProperty("normal")
    vendido = StringProperty("não")
    excluido = BooleanProperty(False)
    lista_ref = ObjectProperty(None)
    lista_lixeira = ObjectProperty(None)
    bg_color = ListProperty([1, 1, 1, 1])
    text_color = ListProperty([0, 0, 0, 1])
    alerta_original = StringProperty("normal")
    data_exclusao = ObjectProperty(allownone=True)

    def on_kv_post(self, base_widget):
        # Garanto que a altura do card seja calculada assim que ele for criado.
        self.atualizar_altura()

    def atualizar_cor(self):
        # Criei esta lógica para mudar a cor do card dependendo do seu estado (vencido, vendido, alerta, etc).
        if self.excluido:
            self.bg_color = [0.3, 0.3, 0.3, 1]
            self.text_color = [1, 1, 1, 1]
        elif self.vendido == "sim":
            self.bg_color = [0, 0.4, 0, 1]
            self.text_color = [1, 1, 1, 1]
        else:
            if self.alerta == "vermelho":
                self.bg_color = [1, 0, 0, 1]
                self.text_color = [1, 1, 1, 1]
            elif self.alerta == "amarelo":
                self.bg_color = [1, 1, 0, 1]
                self.text_color = [0, 0, 0, 1]
            elif self.alerta == "vencido":
                self.bg_color = [0.3, 0.3, 0.3, 1]
                self.text_color = [1, 1, 1, 1]
            else:
                self.bg_color = [1, 1, 1, 1]
                self.text_color = [0, 0, 0, 1]

    def atualizar_interatividade(self):
        # Esta função serve para esconder/desabilitar os botões do card dependendo se ele está na lixeira ou não.
        if not hasattr(self, 'ids'): return
        is_excluido = self.excluido
        if 'btn_x' in self.ids:
            self.ids.btn_x.opacity = 0 if is_excluido else 1
            self.ids.btn_x.disabled = is_excluido

    def atualizar_altura(self):
        # Um ajuste para que a altura do card se adapte ao conteúdo dele.
        if hasattr(self.ids, 'box'):
            self.height = self.ids.box.minimum_height

    def marcar_vendido(self):
        # Ação para quando eu marco um produto como vendido. Mudo o status e chamo a reordenação da lista.
        if self.vendido == "não":
            self.alerta_original = self.alerta
            self.vendido = "sim"
            self.atualizar_cor()
            self.atualizar_interatividade()
            if self.lista_ref and self.parent:
                MainWidget.inserir_com_prioridade(self.lista_ref)

    def desmarcar_vendido(self):
        # Ação para quando eu desmarco um produto como vendido.
        if self.vendido == "sim":
            self.alerta = self.alerta_original
            self.vendido = "não"
            self.atualizar_cor()
            self.atualizar_interatividade()
            if self.lista_ref and self.parent:
                MainWidget.inserir_com_prioridade(self.lista_ref)

    def excluir_produto(self):
        # Ação do botão 'X': remove o card da lista principal e o adiciona na lixeira.
        if self.lista_ref and self.lista_lixeira:
            self.lista_ref.remove_widget(self)
            self.lista_lixeira.add_widget(self)
            self.excluido = True
            self.data_exclusao = datetime.date.today()
            self.atualizar_cor()
            self.atualizar_interatividade()
            if self.parent:
                self.parent.height = self.parent.minimum_height

    def restaurar_produto(self):
        # Ação do botão 'Restaurar': tira o card da lixeira e o coloca de volta na lista principal.
        if self.lista_lixeira and self.lista_ref:
            self.lista_lixeira.remove_widget(self)
            self.excluido = False
            self.data_exclusao = None
            self.atualizar_cor()
            self.atualizar_interatividade()
            self.lista_ref.add_widget(self)
            MainWidget.inserir_com_prioridade(self.lista_ref)


# ================== CLASSE PRINCIPAL DA INTERFACE ==================

class MainWidget(BoxLayout):
    # Aqui eu defino as propriedades que vou usar para o carregamento progressivo da lista.
    todos_os_produtos = ListProperty([])  # Guarda os DADOS de todos os produtos.
    indice_carregamento = NumericProperty(0)  # Controla qual o próximo lote a carregar.
    carregando_mais = BooleanProperty(False)  # Evita carregar vários lotes ao mesmo tempo.

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Assim que a tela principal é criada, eu agendo a limpeza da lixeira para rodar a cada 24h.
        Clock.schedule_interval(lambda dt: self.limpar_lixeira(), 24 * 60 * 60)

    def inicializar_dados(self, produtos_carregados):
        # Esta função prepara os dados que vieram do JSON para serem exibidos.
        self.ids.lista_produtos.clear_widgets()
        self.ids.lista_excluidos.clear_widgets()

        produtos_ativos = [p for p in produtos_carregados if not p.get("excluido", False)]
        produtos_lixeira = [p for p in produtos_carregados if p.get("excluido", False)]

        # Já ordeno a lista principal de uma vez para otimizar.
        hoje = datetime.date.today()
        produtos_ativos.sort(key=lambda p: (p['data_validade'] - hoje).days)

        self.todos_os_produtos = produtos_ativos
        self.indice_carregamento = 0

        # Chamo a função para carregar o primeiro lote de produtos.
        self.carregar_lote_produtos()

        # A lixeira eu carrego de uma vez só, pois geralmente são poucos itens.
        self.carregar_produtos_na_lista(produtos_lixeira, self.ids.lista_excluidos)
        MainWidget.inserir_com_prioridade(self.ids.lista_produtos)

    def carregar_lote_produtos(self):
        # Esta é a mágica do carregamento progressivo: ela cria os widgets só para o próximo lote de produtos.
        if self.carregando_mais:
            return
        self.carregando_mais = True
        fim_lote = self.indice_carregamento + LOTE_DE_CARGA
        proximo_lote = self.todos_os_produtos[self.indice_carregamento:fim_lote]
        if proximo_lote:
            self.carregar_produtos_na_lista(proximo_lote, self.ids.lista_produtos)
            self.indice_carregamento = fim_lote
        self.carregando_mais = False

    def verificar_rolagem(self, scroll_y):
        # Esta função é chamada pelo ScrollView no arquivo .kv sempre que eu rolo a tela.
        # Se a barra de rolagem estiver quase no fim, eu chamo a função para carregar mais produtos.
        if scroll_y < 0.1 and self.indice_carregamento < len(self.todos_os_produtos):
            self.carregar_lote_produtos()

    def carregar_produtos_na_lista(self, lista_de_dados, widget_lista):
        # Criei esta função para não repetir código. Ela pega uma lista de dados e cria os cards na tela.
        hoje = datetime.date.today()
        for p in lista_de_dados:
            data_validade = p["data_validade"]
            dias_restantes = (data_validade - hoje).days
            card = ProductCard(
                nome=p["nome"],
                validade=data_validade.strftime("%d/%m/%Y"),
                dias=str(dias_restantes) if dias_restantes >= 0 else "Vencido",
                troca="Sim" if p["possui_troca"] else "Não",
                vendido=p.get("vendido", "não"),
                alerta_original=p.get("alerta_original", "normal"),
                lista_ref=self.ids.lista_produtos,
                lista_lixeira=self.ids.lista_excluidos
            )
            # Defino o alerta (cor) do card com base na data de validade.
            if not p.get("excluido", False):
                if card.vendido != "sim":
                    if dias_restantes < 0:
                        card.alerta = "vencido"
                    elif dias_restantes <= 3:
                        card.alerta = "vermelho"
                    elif dias_restantes <= 7:
                        card.alerta = "amarelo"
                    else:
                        card.alerta = "normal"
            else:
                card.excluido = True
                card.data_exclusao = p.get("data_exclusao")
            card.atualizar_cor()
            card.atualizar_interatividade()
            widget_lista.add_widget(card)

    @staticmethod
    def inserir_com_prioridade(lista):
        # Esta função é para reordenar a lista na tela, colocando os produtos mais urgentes (alerta vermelho) no topo.
        hoje = datetime.date.today()
        ordem_grupos = ["vermelho", "amarelo", "branco", "vencido", "verde"]
        grupos = {key: [] for key in ordem_grupos}

        for c in lista.children[:]:
            if c.vendido == "sim":
                grupos["verde"].append(c)
            elif c.alerta == "vencido":
                grupos["vencido"].append(c)
            elif c.alerta in grupos:
                grupos[c.alerta].append(c)
            else:
                grupos["branco"].append(c)

        # Dentro de cada grupo de cor, eu também ordeno pela data de vencimento.
        def ordenar_por_vencimento(card):
            try:
                data_venc = datetime.datetime.strptime(card.validade, "%d/%m/%Y").date()
                return (data_venc - hoje).days
            except ValueError:
                return float('inf')

        for key in grupos:
            grupos[key].sort(key=ordenar_por_vencimento)

        lista.clear_widgets()
        for key in ordem_grupos:
            for card in grupos[key]:
                lista.add_widget(card)

    def abrir_popup_novo_produto(self):
        # Criei toda a interface do popup de "Adicionar Produto" aqui no código Python.
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        input_nome = TextInput(hint_text='Nome do produto', multiline=False)
        hoje = datetime.date.today()
        anos = [str(hoje.year + i) for i in range(5)]
        meses = [f"{i:02d}" for i in range(1, 13)]
        dias = [f"{i:02d}" for i in range(1, 32)]
        spinner_ano = Spinner(text=str(hoje.year), values=anos, size_hint_x=0.4)
        spinner_mes = Spinner(text=f"{hoje.month:02d}", values=meses, size_hint_x=0.3)
        spinner_dia = Spinner(text=f"{hoje.day:02d}", values=dias, size_hint_x=0.3)
        spinner_layout = BoxLayout(spacing=5, size_hint_y=None, height='40dp')
        spinner_layout.add_widget(spinner_dia)
        spinner_layout.add_widget(spinner_mes)
        spinner_layout.add_widget(spinner_ano)
        troca_layout = BoxLayout(size_hint_y=None, height='40dp')
        btn_troca_sim = Button(text='Troca: SIM')
        btn_troca_nao = Button(text='Troca: NÃO')
        troca_layout.add_widget(btn_troca_sim)
        troca_layout.add_widget(btn_troca_nao)
        troca_selecao = {'valor': None}

        def selecionar_troca(valor):
            troca_selecao['valor'] = valor
            btn_troca_sim.background_color = (0, 1, 0, 1) if valor else (1, 1, 1, 1)
            btn_troca_nao.background_color = (1, 0, 0, 1) if not valor else (1, 1, 1, 1)

        btn_troca_sim.bind(on_press=lambda x: selecionar_troca(True))
        btn_troca_nao.bind(on_press=lambda x: selecionar_troca(False))
        btn_adicionar = Button(text='Adicionar produto', size_hint_y=None, height='40dp')
        content.add_widget(input_nome)
        content.add_widget(spinner_layout)
        content.add_widget(troca_layout)
        content.add_widget(btn_adicionar)
        popup = Popup(title='Novo Produto', content=content, size_hint=(0.9, 0.6))

        def adicionar_produto_callback(instance):
            # Quando o botão 'Adicionar' do popup é pressionado, eu chamo a minha função que realmente cria o produto.
            self.adicionar_novo_produto(
                nome=input_nome.text,
                ano=spinner_ano.text,
                mes=spinner_mes.text,
                dia=spinner_dia.text,
                troca=troca_selecao['valor']
            )
            popup.dismiss()

        btn_adicionar.bind(on_press=adicionar_produto_callback)
        popup.open()

    def adicionar_novo_produto(self, nome, ano, mes, dia, troca):
        # Esta é a função que pega os dados do popup e cria um novo ProductCard.
        nome = nome.strip()
        if not nome or troca is None: return
        try:
            data_val = datetime.date(int(ano), int(mes), int(dia))
        except ValueError:
            return
        hoje = datetime.date.today()
        dias_restantes = (data_val - hoje).days
        card = ProductCard(nome=nome, validade=data_val.strftime("%d/%m/%Y"),
                           dias=str(dias_restantes) if dias_restantes >= 0 else "Vencido",
                           troca="Sim" if troca else "Não", lista_ref=self.ids.lista_produtos,
                           lista_lixeira=self.ids.lista_excluidos)
        if dias_restantes < 0:
            card.alerta = "vencido"
        elif dias_restantes <= 3:
            card.alerta = "vermelho"
        elif dias_restantes <= 7:
            card.alerta = "amarelo"
        else:
            card.alerta = "normal"
        card.alerta_original = card.alerta
        card.atualizar_cor()
        card.atualizar_interatividade()
        self.ids.lista_produtos.add_widget(card)
        MainWidget.inserir_com_prioridade(self.ids.lista_produtos)

    def limpar_lixeira(self):
        # Esta é a lógica que remove os produtos que estão na lixeira há mais de 7 dias.
        hoje = datetime.date.today()
        to_remove = [c for c in self.ids.lista_excluidos.children if
                     c.data_exclusao and (hoje - c.data_exclusao).days > 7]
        for card in to_remove:
            self.ids.lista_excluidos.remove_widget(card)

    def filtrar_produtos(self, texto):
        # Função para a barra de pesquisa: escondo os cards que não correspondem ao texto digitado.
        texto = texto.strip().lower()
        for card in self.ids.lista_produtos.children:
            if texto in card.nome.lower():
                card.height = card.ids.box.minimum_height
                card.opacity = 1
                card.disabled = False
            else:
                card.height = 0
                card.opacity = 0
                card.disabled = True


# ================== CLASSE PRINCIPAL DO MEU APLICATIVO ==================

class ProdutoApp(App):
    title = "Prazo Certo"

    def build(self):
        # Esta é a função principal que constrói o meu app.
        Window.size = (360, 640)
        Builder.load_file("tela.kv")
        self.root = MainWidget()
        # Aqui eu agendo a transição da tela de splash para a tela principal depois de 3 segundos.
        Clock.schedule_once(self.mudar_para_tela_principal, 3)
        self.root.ids.screen_manager.current = "splash"
        return self.root

    def on_stop(self):
        # Implementei essa função para garantir que, ao fechar o app, eu chame a rotina de salvar os dados.
        print("Salvando dados ao sair...")
        if self.root:
            salvar_todos_produtos(self)

    def mudar_para_tela_principal(self, dt):
        # Esta função faz a transição da tela e chama o carregamento inicial dos dados.
        self.carregar_dados_iniciais()
        self.root.ids.screen_manager.current = "produtos"

    def carregar_dados_iniciais(self):
        # Função que dispara o carregamento dos produtos do arquivo JSON.
        produtos_carregados = carregar_produtos()
        self.root.inicializar_dados(produtos_carregados)


# ================== PONTO DE PARTIDA DO CÓDIGO ==================

if __name__ == "__main__":
    # É aqui que o meu aplicativo começa a rodar.
    ProdutoApp().run()