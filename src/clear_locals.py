#Função só pra facilitar testes, para limpar os locais simulados de cada nó
import os
import shutil

src_dir = os.path.dirname(os.path.abspath(__file__))
def clear_locals():

    
    locals_dir = os.path.join(src_dir, "Locals")
    if os.path.exists(locals_dir):
        for item in os.listdir(locals_dir):
            item_path = os.path.join(locals_dir, item)

            if os.path.isdir(item_path) and item != "Rank 0":
                try:
                    shutil.rmtree(item_path)
                except Exception as e:
                    print(f"[Clear] Erro ao deletar {item_path}: {e}")


            #no Rank 0, mantemos apenas o arquivo NPZ
            elif os.path.isdir(item_path) and item == "Rank 0":
                for file_item in os.listdir(item_path):
                    if not file_item.endswith(".npz"):
                        file_path = os.path.join(item_path, file_item)
                        try:
                            if os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                            else:
                                os.remove(file_path)
                        except Exception as e:
                            pass
                    
clear_locals()