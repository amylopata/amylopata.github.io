<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" version="3.16.4-Hannover" hasScaleBasedVisibilityFlag="0" maxScale="0" minScale="1e+08">
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
      <resampling maxOversampling="2" zoomedInResamplingMethod="nearestNeighbour" enabled="false" zoomedOutResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer classificationMin="0" type="singlebandpseudocolor" nodataColor="" band="1" alphaBand="-1" classificationMax="8.33" opacity="1">
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
        <colorrampshader minimumValue="0" clip="0" classificationMode="1" colorRampType="DISCRETE" maximumValue="8.33" labelPrecision="4">
          <colorramp type="gradient" name="[source]">
            <prop k="color1" v="255,251,156,255"/>
            <prop k="color2" v="0,25,255,255"/>
            <prop k="discrete" v="1"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.2;253,174,97,255:0.4;255,255,191,255:0.6;171,221,164,255:0.8;248,33,0,255"/>
          </colorramp>
          <item label="&lt;= 5.0000" value="5" color="#648fff" alpha="255"/>
          <item label="5.0000 - 8.3300" value="8.33" color="#785ef0" alpha="255"/>
          <item label="8.3300 - 35.0000" value="35" color="#dc267f" alpha="255"/>
          <item label="> 35.0000" value="inf" color="#000000" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast gamma="1" brightness="0" contrast="0"/>
    <huesaturation colorizeStrength="100" colorizeOn="0" saturation="0" colorizeRed="255" colorizeGreen="128" grayscaleMode="0" colorizeBlue="128"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
