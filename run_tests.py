import os
import pytest

if __name__ == '__main__':
    pytest.main([
        "-s", "-v",
        "--alluredir=reports/allure-results"
    ])
    os.system("allure generate reports/allure-results -o reports/allure-report --clean")
