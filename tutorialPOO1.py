class Televisão: 
    def __init__(self,):
        self.marca = 'marca'
        self.tamanho = 'tamanho'
        self.canal = 1
        self.volume = 10
        self.ligada = False

    def modelo(self):
        self.marca = input("Digite a marca da televisão: ")
        print(f'Sua marca é {self.marca}')
    def ligar(self):
        self.ligada = True
        print(f"A televisão {self.marca} está ligada.")

    def desligar(self):
        self.ligada = False
        print(f"A televisão {self.marca} está desligada.")

    def mudar_canal(self, novo_canal):
        if self.ligada:
            self.canal = novo_canal
            print(f"Canal alterado para {self.canal}.")
        else:
            print("A televisão está desligada. Ligue-a primeiro.")

    def aumentar_volume(self):
        if self.ligada:
            self.volume += 1
            print(f"Volume aumentado para {self.volume}.")
        else:
            print("A televisão está desligada. Ligue-a primeiro.")

    def diminuir_volume(self):
        if self.ligada:
            self.volume -= 1
            print(f"Volume diminuído para {self.volume}.")
        else:
            print("A televisão está desligada. Ligue-a primeiro.")
    def __str__(self):
        estado = "ligada" if self.ligada else "desligada"
        return (f"Televisão {self.marca} ({self.tamanho}) - "
                f"Estado: {estado}, Canal: {self.canal}, Volume: {self.volume}")
    

#Teste televisão ligar/desligar

tv_teste = Televisão()
if tv_teste.ligada == False:
    tv_teste.ligada = "Desligada"
else:
    tv_teste.ligada = "Ligada"
print(f"Estado inicial da TV: {tv_teste.ligada}")  # Deve ser False
tv_teste.ligar()
tv_teste.modelo()

#Teste aumentar volume

if tv_teste.volume == 10:
    print(f"A tv está no volume padrão")
resp = input("Deseja alterar o volume? (s/n): ")
if resp == 's':  
    qual = input("Deseja aumentar ou diminuir o volume? (a/d): ")
    if qual == 'a':
        tv_teste.aumentar_volume()
    elif qual == 'd':
        tv_teste.diminuir_volume()
        
if resp == 'n':
    print(f"O volume permanece em {tv_teste.volume}")

#Teste mudar canal
resp2 = input("Deseja mudar o canal? (s/n): ")
if resp2 == 's':
    print(f"Canal atual: {tv_teste.canal}")
    novo_canal = int(input("Digite o novo canal: "))
    tv_teste.mudar_canal(novo_canal)