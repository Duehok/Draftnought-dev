TURRETS = ["1", "2", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
           "Q", "R", "S", "T", "V", "W", "X", "Y", "3", "4"]

TURRET_SCHEMA = (
{
  "$schema" : "http://json-schema.org/draft-04/schema#",
  "patternProperties":
  {
    ".*": { "$ref":"#/definitions/turret"}
  },
  "required": TURRETS,
  "definitions":
  {  
    "turret":
    {
      "type":"object", 
      "properties":
      {
        "to_bow": {"type":"boolean"},
        "positions":
        {
          "type": "array",
          "items":
          {
            "types":"array",
            "items":[{ "type":"number"},{ "type":"number"}]
          },
          "maxItems":4,
          "minItems":1
        }
      }
    }
  }
})
_DEFAULT_TURRET_POSITION = {"positions": [(1000, 1000), (1000, 1000), (1000, 1000), (1000, 1000)],
                           "to_bow": True}
DEFAULT_TURRET_POSITIONS = {turret:_DEFAULT_TURRET_POSITION for turret in TURRETS}
