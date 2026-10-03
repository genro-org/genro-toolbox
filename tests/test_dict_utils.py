"""Tests for dict utility helpers."""


class TestDictExtract:
    """Tests for legacy dictExtract function."""

    def test_basic_extraction(self):
        """Test basic prefix extraction."""
        from genro_toolbox.dict_utils import dictExtract

        data = {"db_host": "localhost", "db_port": 5432, "app_name": "test"}
        result = dictExtract(data, "db_")
        assert result == {"host": "localhost", "port": 5432}
        # Original dict unchanged
        assert "db_host" in data

    def test_pop_removes_from_source(self):
        """Test pop=True removes items from source dict."""
        from genro_toolbox.dict_utils import dictExtract

        data = {"db_host": "localhost", "db_port": 5432, "app_name": "test"}
        result = dictExtract(data, "db_", pop=True)
        assert result == {"host": "localhost", "port": 5432}
        # Items removed from original
        assert "db_host" not in data
        assert "app_name" in data

    def test_slice_prefix_false(self):
        """Test slice_prefix=False keeps full key names."""
        from genro_toolbox.dict_utils import dictExtract

        data = {"db_host": "localhost", "db_port": 5432}
        result = dictExtract(data, "db_", slice_prefix=False)
        assert result == {"db_host": "localhost", "db_port": 5432}

    def test_reserved_name_class(self):
        """Test that 'class' key is renamed to '_class'."""
        from genro_toolbox.dict_utils import dictExtract

        data = {"widget_class": "Button", "widget_name": "submit"}
        result = dictExtract(data, "widget_")
        assert result == {"_class": "Button", "name": "submit"}
