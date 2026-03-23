"""
Script para criar o usuário admin padrão.
Execute com: python -c "from src.create_admin import create_admin; create_admin()"
Ou dentro do contexto do app Flask.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def create_admin():
    """Cria o usuário admin padrão se não existir"""
    from src.main import app
    from src.models.user import User, db
    
    with app.app_context():
        # Verificar se admin já existe
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("✓ Usuário admin já existe")
            return
        
        # Criar admin
        admin = User(
            username='admin',
            email='admin@lachapa.com',
            role='admin'
        )
        admin.set_password('123456')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✓ Usuário admin criado com sucesso")
        print("  Username: admin")
        print("  Email: admin@lachapa.com")
        print("  Senha: 123456")
        print("  ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")

if __name__ == '__main__':
    create_admin()
