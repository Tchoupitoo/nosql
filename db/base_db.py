from abc import ABC, abstractmethod
from datetime import datetime
from faker import Faker
import random

fake = Faker()

class base_db(ABC):
    @abstractmethod
    def clear_db(self):
        pass

    @abstractmethod
    def init_db(self):
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
    def db_size(self):
        pass

    @abstractmethod
    def request1(self):
        pass

    @abstractmethod
    def request2(self):
        pass

    @abstractmethod
    def request3(self):
        pass

    @abstractmethod
    def request4(self):
        pass