from abc import ABC, abstractmethod

from faker import Faker

fake = Faker()


class base_db(ABC):

    @abstractmethod
    def init_db(self):
        pass

    @abstractmethod
    def clear_db(self):
        pass

    @abstractmethod
    def create_users(self, num_users):
        pass

    @abstractmethod
    def create_produits(self, num_produits):
        pass

    @abstractmethod
    def create_achats(self, num_achats):
        pass

    @abstractmethod
    def select_users(self, num_users):
        pass

    @abstractmethod
    def select_produits(self, num_produits):
        pass

    @abstractmethod
    def db_size(self):
        pass

    @abstractmethod
    def requestGlobalFollows(self):
        pass

    @abstractmethod
    def requestGlobalAchatsByProduit(self):
        pass

    @abstractmethod
    def requestSpecific1(self, user_id, max_level=3):
        pass

    @abstractmethod
    def requestSpecific2(self, user_id, product_id, max_level=3):
        pass

    @abstractmethod
    def requestSpecific3(self, product_id, max_level=3):
        pass
