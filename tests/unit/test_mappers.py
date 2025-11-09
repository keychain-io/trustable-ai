"""
Unit tests for Type and Field Mappers.

Tests the Azure DevOps type and field mapping systems.
"""
import pytest

from adapters.azure_devops.type_mapper import WorkItemTypeMapper, get_platform_type
from adapters.azure_devops.field_mapper import (
    FieldMapper,
    AzureDevOpsFieldBuilder,
    map_fields,
    create_field_builder,
)


@pytest.mark.unit
class TestWorkItemTypeMapper:
    """Test suite for WorkItemTypeMapper."""

    def test_default_scrum_mappings(self):
        """Test default Scrum process template mappings."""
        mapper = WorkItemTypeMapper()

        assert mapper.to_platform_type("epic") == "Epic"
        assert mapper.to_platform_type("feature") == "Feature"
        assert mapper.to_platform_type("story") == "User Story"
        assert mapper.to_platform_type("task") == "Task"
        assert mapper.to_platform_type("bug") == "Bug"

    def test_agile_process_template(self):
        """Test Agile process template mappings."""
        mapper = WorkItemTypeMapper(process_template="agile")

        assert mapper.to_platform_type("story") == "User Story"
        assert mapper.to_platform_type("issue") == "Issue"

    def test_cmmi_process_template(self):
        """Test CMMI process template mappings."""
        mapper = WorkItemTypeMapper(process_template="cmmi")

        assert mapper.to_platform_type("story") == "Requirement"
        assert mapper.to_platform_type("risk") == "Risk"
        assert mapper.to_platform_type("review") == "Review"

    def test_basic_process_template(self):
        """Test Basic process template mappings."""
        mapper = WorkItemTypeMapper(process_template="basic")

        assert mapper.to_platform_type("story") == "Issue"
        assert mapper.to_platform_type("task") == "Issue"
        assert mapper.to_platform_type("bug") == "Issue"

    def test_custom_mappings(self):
        """Test custom type mappings."""
        custom_config = {"story": "Custom Story Type"}
        mapper = WorkItemTypeMapper(config=custom_config)

        assert mapper.to_platform_type("story") == "Custom Story Type"

    def test_case_insensitive(self):
        """Test that type mapping is case-insensitive."""
        mapper = WorkItemTypeMapper()

        assert mapper.to_platform_type("Epic") == "Epic"
        assert mapper.to_platform_type("EPIC") == "Epic"
        assert mapper.to_platform_type("epic") == "Epic"

    def test_unknown_type_raises_error(self):
        """Test that unknown type raises ValueError."""
        mapper = WorkItemTypeMapper()

        with pytest.raises(ValueError, match="Unknown generic type"):
            mapper.to_platform_type("unknown-type")

    def test_to_generic_type(self):
        """Test reverse mapping from platform to generic type."""
        mapper = WorkItemTypeMapper()

        assert mapper.to_generic_type("Epic") == "epic"
        assert mapper.to_generic_type("User Story") == "story"
        assert mapper.to_generic_type("Task") == "task"

    def test_to_generic_type_unknown(self):
        """Test reverse mapping with unknown platform type."""
        mapper = WorkItemTypeMapper()

        with pytest.raises(ValueError, match="Unknown platform type"):
            mapper.to_generic_type("Unknown Type")

    def test_is_valid_generic_type(self):
        """Test validation of generic types."""
        mapper = WorkItemTypeMapper()

        assert mapper.is_valid_generic_type("epic") is True
        assert mapper.is_valid_generic_type("story") is True
        assert mapper.is_valid_generic_type("unknown") is False

    def test_is_valid_platform_type(self):
        """Test validation of platform types."""
        mapper = WorkItemTypeMapper()

        assert mapper.is_valid_platform_type("Epic") is True
        assert mapper.is_valid_platform_type("User Story") is True
        assert mapper.is_valid_platform_type("Unknown") is False

    def test_get_available_types(self):
        """Test getting all available type mappings."""
        mapper = WorkItemTypeMapper()
        types = mapper.get_available_types()

        assert isinstance(types, dict)
        assert "epic" in types
        assert types["epic"] == "Epic"


@pytest.mark.unit
class TestWorkItemTypeMapperConvenience:
    """Test convenience functions for type mapper."""

    def test_get_platform_type_function(self):
        """Test get_platform_type convenience function."""
        platform_type = get_platform_type("story")

        assert platform_type == "User Story"

    def test_get_platform_type_with_config(self):
        """Test get_platform_type with custom config."""
        config = {"story": "Custom Story"}
        platform_type = get_platform_type("story", config)

        assert platform_type == "Custom Story"


@pytest.mark.unit
class TestFieldMapper:
    """Test suite for FieldMapper."""

    def test_standard_fields(self):
        """Test standard field mappings."""
        mapper = FieldMapper()

        assert mapper.get_field_name("title") == "System.Title"
        assert mapper.get_field_name("description") == "System.Description"
        assert mapper.get_field_name("state") == "System.State"
        assert mapper.get_field_name("assigned_to") == "System.AssignedTo"
        assert mapper.get_field_name("story_points") == "Microsoft.VSTS.Scheduling.StoryPoints"

    def test_custom_fields(self):
        """Test custom field mappings."""
        custom_fields = {
            "business_value": "Custom.BusinessValueScore",
            "roi": "Custom.ROI",
        }
        mapper = FieldMapper(custom_fields=custom_fields)

        assert mapper.get_field_name("business_value") == "Custom.BusinessValueScore"
        assert mapper.get_field_name("roi") == "Custom.ROI"

    def test_custom_fields_take_precedence(self):
        """Test that custom fields override standard fields."""
        custom_fields = {"title": "Custom.Title"}
        mapper = FieldMapper(custom_fields=custom_fields)

        assert mapper.get_field_name("title") == "Custom.Title"

    def test_unknown_field_raises_error(self):
        """Test that unknown field raises ValueError."""
        mapper = FieldMapper()

        with pytest.raises(ValueError, match="Unknown field"):
            mapper.get_field_name("unknown_field")

    def test_map_fields(self):
        """Test mapping a dictionary of fields."""
        mapper = FieldMapper()
        generic_fields = {
            "title": "Test Title",
            "description": "Test Description",
            "story_points": 5,
        }

        mapped = mapper.map_fields(generic_fields)

        assert mapped["System.Title"] == "Test Title"
        assert mapped["System.Description"] == "Test Description"
        assert mapped["Microsoft.VSTS.Scheduling.StoryPoints"] == 5

    def test_map_fields_with_platform_format(self):
        """Test that fields already in platform format pass through."""
        mapper = FieldMapper()
        fields = {
            "title": "Test",
            "System.Tags": "tag1; tag2",  # Already platform format
        }

        mapped = mapper.map_fields(fields)

        assert mapped["System.Title"] == "Test"
        assert mapped["System.Tags"] == "tag1; tag2"

    def test_reverse_map_fields(self):
        """Test reverse mapping from platform to generic fields."""
        mapper = FieldMapper()
        platform_fields = {
            "System.Title": "Test Title",
            "System.Description": "Test Description",
            "Microsoft.VSTS.Scheduling.StoryPoints": 5,
        }

        generic = mapper.reverse_map_fields(platform_fields)

        assert generic["title"] == "Test Title"
        assert generic["description"] == "Test Description"
        assert generic["story_points"] == 5

    def test_is_custom_field(self):
        """Test checking if field is custom."""
        custom_fields = {"business_value": "Custom.BusinessValue"}
        mapper = FieldMapper(custom_fields=custom_fields)

        assert mapper.is_custom_field("business_value") is True
        assert mapper.is_custom_field("title") is False

    def test_get_available_fields(self):
        """Test getting all available field mappings."""
        custom_fields = {"business_value": "Custom.BusinessValue"}
        mapper = FieldMapper(custom_fields=custom_fields)

        fields = mapper.get_available_fields()

        assert "title" in fields
        assert "business_value" in fields
        assert fields["business_value"] == "Custom.BusinessValue"


@pytest.mark.unit
class TestAzureDevOpsFieldBuilder:
    """Test suite for AzureDevOpsFieldBuilder."""

    def test_fluent_interface(self):
        """Test fluent interface for building fields."""
        builder = AzureDevOpsFieldBuilder()

        result = (
            builder
            .set("title", "Test Title")
            .set("description", "Test Description")
            .set("story_points", 5)
            .build()
        )

        assert result["System.Title"] == "Test Title"
        assert result["System.Description"] == "Test Description"
        assert result["Microsoft.VSTS.Scheduling.StoryPoints"] == 5

    def test_set_custom(self):
        """Test setting custom fields directly."""
        builder = AzureDevOpsFieldBuilder()

        result = (
            builder
            .set_custom("Custom.BusinessValue", 100)
            .set_custom("Custom.ROI", "High")
            .build()
        )

        assert result["Custom.BusinessValue"] == 100
        assert result["Custom.ROI"] == "High"

    def test_set_multiple(self):
        """Test setting multiple fields at once."""
        builder = AzureDevOpsFieldBuilder()

        fields = {
            "title": "Test",
            "description": "Description",
            "priority": 1,
        }

        result = builder.set_multiple(fields).build()

        assert result["System.Title"] == "Test"
        assert result["System.Description"] == "Description"
        assert result["Microsoft.VSTS.Common.Priority"] == 1

    def test_clear(self):
        """Test clearing all fields."""
        builder = AzureDevOpsFieldBuilder()

        builder.set("title", "Test").clear()
        result = builder.build()

        assert len(result) == 0

    def test_with_custom_field_mapper(self):
        """Test builder with custom field mapper."""
        custom_fields = {"business_value": "Custom.BusinessValue"}
        mapper = FieldMapper(custom_fields=custom_fields)
        builder = AzureDevOpsFieldBuilder(mapper)

        result = builder.set("business_value", 100).build()

        assert result["Custom.BusinessValue"] == 100


@pytest.mark.unit
class TestFieldMapperConvenience:
    """Test convenience functions for field mapper."""

    def test_map_fields_function(self):
        """Test map_fields convenience function."""
        generic_fields = {"title": "Test", "story_points": 5}

        mapped = map_fields(generic_fields)

        assert mapped["System.Title"] == "Test"
        assert mapped["Microsoft.VSTS.Scheduling.StoryPoints"] == 5

    def test_map_fields_with_custom(self):
        """Test map_fields with custom field mappings."""
        generic_fields = {"business_value": 100}
        custom_fields = {"business_value": "Custom.BusinessValue"}

        mapped = map_fields(generic_fields, custom_fields)

        assert mapped["Custom.BusinessValue"] == 100

    def test_create_field_builder_function(self):
        """Test create_field_builder convenience function."""
        builder = create_field_builder()

        assert isinstance(builder, AzureDevOpsFieldBuilder)

        result = builder.set("title", "Test").build()
        assert result["System.Title"] == "Test"
