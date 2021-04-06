<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" version="3.16.4-Hannover" minScale="1e+08" maxScale="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal enabled="0" fetchMode="0" mode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property value="false" key="WMSBackgroundLayer"/>
    <property value="false" key="WMSPublishDataSourceUrl"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property value="Value" key="identify/format"/>
  </customproperties>
  <pipe>
    <provider>
      <resampling enabled="false" maxOversampling="2" zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer classificationMin="0" band="1" classificationMax="8.33" alphaBand="-1" opacity="1" nodataColor="" type="singlebandpseudocolor">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader labelPrecision="4" classificationMode="1" maximumValue="8.33" clip="0" minimumValue="0" colorRampType="DISCRETE">
          <colorramp name="[source]" type="gradient">
            <prop k="color1" v="255,251,156,255"/>
            <prop k="color2" v="0,25,255,255"/>
            <prop k="discrete" v="1"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.2;253,174,97,255:0.4;255,255,191,255:0.6;171,221,164,255:0.8;248,33,0,255"/>
          </colorramp>
          <item label="&lt;= 5.0000" value="5" alpha="255" color="#ddcc77"/>
          <item label="5.0000 - 8.3300" value="8.33" alpha="255" color="#65b0d6"/>
          <item label="8.3300 - 35.0000" value="35" alpha="255" color="#882255"/>
          <item label="> 35.0000" value="inf" alpha="255" color="#000000"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast gamma="1" contrast="0" brightness="0"/>
    <huesaturation colorizeRed="255" grayscaleMode="0" colorizeStrength="100" colorizeOn="0" colorizeBlue="128" saturation="0" colorizeGreen="128"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
